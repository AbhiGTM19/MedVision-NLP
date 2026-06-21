from pydantic import BaseModel

class RetrievedChunk(BaseModel):
    content: str
    source: str
    specialty: str | None
    document_type: str  # "drug", "abbreviation", "guideline"
    relevance_score: float
