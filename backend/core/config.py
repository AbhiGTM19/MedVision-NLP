import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "MedVision NLP API"
    VERSION: str = "1.0.0"
    ENV: str = os.getenv("ENV", "local")  # 'local' or 'prod'
    
    # Remote Hugging Face Model Repository
    HF_MODEL_REPO_ID: str = "abhshkgtm19/Healthcare-NLP-Models"
    
    # Pre-trained Transformer configurations
    HF_TRANSFORMER_MODEL_ID: str = os.getenv("HF_TRANSFORMER_MODEL_ID", "emilyalsentzer/Bio_ClinicalBERT")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
