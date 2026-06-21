from typing import List, Optional

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="The clinical notes text to process")

class WordAttribution(BaseModel):
    word: str
    score: float

class PredictionResponse(BaseModel):
    specialty: str
    confidence: float
    word_attributions: List[WordAttribution] = []
    extracted_text: Optional[str] = None
    error: Optional[str] = None

class RAGResponse(BaseModel):
    answer: str
    sources: List[str] = []
    error: Optional[str] = None

class PredictionRAGResponse(BaseModel):
    specialty: str
    confidence: float
    word_attributions: List[WordAttribution] = []
    extracted_text: Optional[str] = None
    rag_response: RAGResponse

class ChatMessage(BaseModel):
    role: str # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

