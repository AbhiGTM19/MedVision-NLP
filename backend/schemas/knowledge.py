from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    content: str
    source: str
    specialty: str | None = None
    document_type: str = "Unknown"  # "drug", "abbreviation", "guideline", "textbook"
    layer: str = "foundation"
    relevance_score: float
