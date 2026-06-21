import os
from google import genai
from google.genai import types

from core.config import settings
from schemas.predict import ChatMessage, RAGResponse
from services.knowledge_service import knowledge_service

class LLMService:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self.model_id = "gemini-2.5-flash"
        else:
            self.client = None

    def generate_rag_response(self, query: str, specialty: str | None = None) -> RAGResponse:
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
Use the following retrieved context to answer the user's clinical query. If the context does not contain the answer, say so, but you may still provide general medical knowledge while making it clear it wasn't in the specific guidelines provided.

Context:
{context_text}

Query: {query}
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                ),
            )
            return RAGResponse(answer=response.text, sources=sources)
        except Exception as e:
            return RAGResponse(answer="Failed to generate response.", error=str(e))

    def generate_chat_response(self, messages: list[ChatMessage]) -> str:
        if not self.client:
            return "LLM is not configured (Missing API Key)."
            
        try:
            # We need to format messages for the Gemini API
            gemini_messages = []
            for msg in messages:
                role = "user" if msg.role == "user" else "model"
                gemini_messages.append({"role": role, "parts": [{"text": msg.content}]})
                
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=gemini_messages,
            )
            return response.text
        except Exception as e:
            return f"Error: {e}"

llm_service = LLMService()
