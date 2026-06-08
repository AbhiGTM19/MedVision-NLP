from typing import List, Optional
from pydantic import BaseModel, Field

class PredictionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="The clinical notes text to process")

class EntitySchema(BaseModel):
    word: str
    tag: str
    confidence: Optional[float] = None

class PredictionResponse(BaseModel):
    entities: List[EntitySchema]
    extracted_text: Optional[str] = None
    error: Optional[str] = None
