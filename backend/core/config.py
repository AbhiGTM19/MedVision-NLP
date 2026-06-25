import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "MedVision NLP API"
    VERSION: str = "1.0.0"
    ENV: str = os.getenv("ENV", "local")  # 'local' or 'prod'
    
    # Remote Hugging Face Model Repository
    HF_MODEL_REPO_ID: str = "abhshkgtm19/medvision-models"
    
    # Pre-trained Transformer configurations
    HF_TRANSFORMER_MODEL_ID: str = os.getenv("HF_TRANSFORMER_MODEL_ID", "emilyalsentzer/Bio_ClinicalBERT")

    # LLM Integration
    GEMINI_API_KEY: str | None = None

    # Persistent Storage
    STORAGE_PATH: str = "/data/chroma_db" if Path("/data").exists() else str(BASE_DIR / "data" / "chroma_db")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
