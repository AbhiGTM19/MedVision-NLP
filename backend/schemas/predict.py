from typing import Dict, Optional

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="The clinical notes text")
    model_choice: str = Field(default="fast", description="The model to use: 'fast' or 'accurate'")

class PredictionResponse(BaseModel):
    prediction: str
    confidence: float
    explanation: str
    word_importances: Dict[str, float] = {}
    model_used: str
    error: Optional[str] = None
