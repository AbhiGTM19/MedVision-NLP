import inspect
import logging
import os
import re

from google import genai
from google.genai import types

from core.config import settings
from core.prompts import RAG_SYSTEM_PROMPT, build_chat_system_prompt
from schemas.predict import ChatMessage, RAGResponse
from services.knowledge_service import knowledge_service

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self.model_id = "gemini-3.1-flash-lite"
            logger.info("LLMService initialized with Gemini client.")
        else:
            self.client = None
            logger.warning("GEMINI_API_KEY is not set. LLMService is disabled.")

    async def generate_rag_response(self, query: str, specialty: str | None = None) -> RAGResponse:
        if not self.client:
            return RAGResponse(answer="LLM is not configured (Missing API Key). RAG is disabled.", error="Missing API Key")

        # 1. Retrieve knowledge
        chunks = knowledge_service.retrieve_context(query, specialty=specialty, top_k=5)
        
        # 2. Build context
        sources = list(set([c.source for c in chunks]))
        source_map = {source: idx + 1 for idx, source in enumerate(sources)}
        context_text = "\n\n".join([f"[{source_map[c.source]}] Source: {c.source}\nContent: {c.content}" for c in chunks])

        # 3. Construct prompt
        prompt = RAG_SYSTEM_PROMPT.format(context_text=context_text, query=query)

        try:
            # We use the async client method to avoid blocking Uvicorn
            response = await self.client.aio.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                ),
            )
            answer_text = response.text
            
            # Phase 4: Regex Dosing Interceptor Safety Guardrail
            if re.search(r'\d+\.?\d*\s?(mg|mcg|mL|g|IU)', answer_text, re.IGNORECASE):
                warning_msg = "\n\n> [!CAUTION]\n> **CRITICAL SAFETY WARNING:** A drug dosage was detected in this response. You MUST cross-reference all drug doses with the National Formulary of India (NFI) before clinical application."
                answer_text += warning_msg
                
            # Add universal disclaimer
            disclaimer = "\n\n---\n\n> [!CAUTION]\n> **Disclaimer:** This response is AI-generated for informational purposes only. It is NOT a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider for clinical decisions. Verify all drug dosages against the National Formulary of India (NFI)."
            answer_text += disclaimer
                
            return RAGResponse(answer=answer_text, sources=sources)
        except Exception as e:
            logger.error(f"Failed to generate RAG response: {e}", exc_info=True)
            return RAGResponse(answer="Failed to generate response.", error=str(e))

    async def generate_chat_response_stream(self, messages: list[ChatMessage]):
        if not self.client:
            import json
            yield f"data: {json.dumps({'error': 'LLM is not configured (Missing API Key).'})}\n\n"
            return
            
        try:
            # 1. RAG Retrieval on the last user message
            last_user_msg = next((m.content for m in reversed(messages) if m.role == 'user'), "")
            context_text = ""
            sources = []
            if last_user_msg:
                chunks = knowledge_service.retrieve_context(last_user_msg, top_k=5)
                sources = list(set([c.source for c in chunks]))
                source_map = {source: idx + 1 for idx, source in enumerate(sources)}
                context_text = "\n\n".join([f"[{source_map[c.source]}] Source: {c.source}\nContent: {c.content}" for c in chunks])

            import json
            # Yield the sources first so the frontend can display them in the context drawer
            yield f"data: {json.dumps({'sources': sources, 'context_preview': context_text})}\n\n"

            # 2. System prompt for chat
            system_prompt = build_chat_system_prompt(context_text)
            
            gemini_messages = [{"role": "user", "parts": [{"text": system_prompt}]}, {"role": "model", "parts": [{"text": "Understood. I will strictly act as a Medical AI Assistant and decline non-medical questions."}]}]
            
            for msg in messages:
                role = "user" if msg.role == "user" else "model"
                gemini_messages.append({"role": role, "parts": [{"text": msg.content}]})
                
            # 3. Token Truncation (using Gemini native token counting)
            MAX_TOKENS = 15000
            while len(gemini_messages) > 3:
                try:
                    token_count_response = await self.client.aio.models.count_tokens(
                        model=self.model_id,
                        contents=gemini_messages
                    )
                    if token_count_response.total_tokens <= MAX_TOKENS:
                        break
                except Exception as e:
                    logger.warning(f"Token counting API failed (likely quota limit). Bypassing truncation: {e}")
                    break
                    
                # Remove the oldest user-model pair to keep alternating roles valid
                logger.info(f"Context exceeds {MAX_TOKENS} tokens. Truncating oldest interaction.")
                gemini_messages = gemini_messages[:2] + gemini_messages[4:]
                
            response = self.client.aio.models.generate_content_stream(
                model=self.model_id,
                contents=gemini_messages,
            )
            
            if inspect.iscoroutine(response):
                response = await response
                
            iterator = response.__aiter__()
            if inspect.iscoroutine(iterator):
                iterator = await iterator
                
            full_response = ""
            try:
                async for chunk in response:
                    try:
                        text = chunk.text
                        if text:
                            full_response += text
                            yield f"data: {json.dumps({'text': text})}\n\n"
                    except ValueError:
                        # Safety filter might cause chunk.text to raise ValueError
                        continue
            except Exception as stream_err:
                logger.warning(f"Stream iteration interrupted: {stream_err}")
            # Phase 4: Regex Dosing Interceptor Safety Guardrail (Streaming)
            if re.search(r'\d+\.?\d*\s?(mg|mcg|mL|g|IU)', full_response, re.IGNORECASE):
                warning_msg = "\n\n> [!CAUTION]\n> **CRITICAL SAFETY WARNING:** A drug dosage was detected in this response. You MUST cross-reference all drug doses with the National Formulary of India (NFI) before clinical application."
                yield f"data: {json.dumps({'text': warning_msg})}\n\n"
                
            # Add universal disclaimer at the end
            disclaimer = "\n\n---\n\n> [!CAUTION]\n> **Disclaimer:** This response is AI-generated for informational purposes only. It is NOT a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider for clinical decisions. Verify all drug dosages against the National Formulary of India (NFI)."
            yield f"data: {json.dumps({'text': disclaimer})}\n\n"

        except Exception as e:
            logger.error(f"Failed to generate Chat response: {e}", exc_info=True)
            import json
            fallback_msg = f"\n\n**[System Alert: 3rd-Party LLM API Error ({str(e)[:50]})]**\n\nThe GenAI service is currently rate-limited or unavailable. However, your local RAG Vector Database successfully retrieved the following raw clinical context:\n\n---\n{context_text}\n---"
            yield f"data: {json.dumps({'text': fallback_msg})}\n\n"

llm_service = LLMService()
