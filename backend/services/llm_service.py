import inspect
import logging
import os

from google import genai
from google.genai import types

from core.config import settings
from schemas.predict import ChatMessage, RAGResponse
from services.knowledge_service import knowledge_service

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self.model_id = "gemini-2.5-flash"
            logger.info("LLMService initialized with Gemini client.")
        else:
            self.client = None
            logger.warning("GOOGLE_API_KEY is not set. LLMService is disabled.")

    async def generate_rag_response(self, query: str, specialty: str | None = None) -> RAGResponse:
        if not self.client:
            return RAGResponse(answer="LLM is not configured (Missing API Key). RAG is disabled.", error="Missing API Key")

        # 1. Retrieve knowledge
        chunks = knowledge_service.retrieve_context(query, specialty=specialty, top_k=5)
        
        # 2. Build context
        context_text = "\n\n".join([f"Source: {c.source}\nContent: {c.content}" for c in chunks])
        sources = list(set([c.source for c in chunks]))

        # 3. Construct prompt
        prompt = f"""
You are a highly capable Medical AI Assistant.
Use the following retrieved context to answer the user's clinical query. 

CRITICAL INSTRUCTIONS:
1. You MUST ONLY answer medical or clinical queries. If the user's query is not related to medicine, clinical guidelines, or healthcare, you must politely decline to answer.
2. If the context does not contain the exact answer, you may provide general medical knowledge, but you must clearly state that it was not found in the specific guidelines provided.
3. You MUST provide inline citations (e.g., [1], [2]) in your text whenever you state a fact or guideline that comes from the provided context. The citations should map to the specific sources listed below.

Context:
{context_text}

Query: {query}
"""

        try:
            # We use the async client method to avoid blocking Uvicorn
            response = await self.client.aio.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                ),
            )
            return RAGResponse(answer=response.text, sources=sources)
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
                context_text = "\n\n".join([f"Source: {c.source}\nContent: {c.content}" for c in chunks])
                sources = list(set([c.source for c in chunks]))

            import json
            # Yield the sources first so the frontend can display them in the context drawer
            yield f"data: {json.dumps({'sources': sources, 'context_preview': context_text[:500] + '...' if len(context_text) > 500 else context_text})}\n\n"

            # 2. System prompt for chat
            system_prompt = "You are a Medical AI Assistant. ONLY answer medical/clinical questions. If asked non-medical questions, politely decline. Provide inline citations (e.g. [1]) if you pull facts from any provided medical context."
            if context_text:
                system_prompt += f"\n\nHere is the retrieved medical context for the user's latest query:\n{context_text}"
            
            gemini_messages = [{"role": "user", "parts": [{"text": system_prompt}]}, {"role": "model", "parts": [{"text": "Understood. I will strictly act as a Medical AI Assistant and decline non-medical questions."}]}]
            
            for msg in messages:
                role = "user" if msg.role == "user" else "model"
                gemini_messages.append({"role": role, "parts": [{"text": msg.content}]})
                
            response = self.client.aio.models.generate_content_stream(
                model=self.model_id,
                contents=gemini_messages,
            )
            
            if inspect.iscoroutine(response):
                response = await response
                
            iterator = response.__aiter__()
            if inspect.iscoroutine(iterator):
                iterator = await iterator
                
            while True:
                try:
                    chunk = await anext(iterator)
                    if chunk.text:
                        yield f"data: {json.dumps({'text': chunk.text})}\n\n"
                except StopAsyncIteration:
                    break
        except Exception as e:
            logger.error(f"Failed to generate Chat response: {e}", exc_info=True)
            import json
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

llm_service = LLMService()
