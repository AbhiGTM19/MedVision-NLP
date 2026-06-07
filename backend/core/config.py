import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "MedVision NLP API"
    VERSION: str = "1.0.0"
    ENV: str = os.getenv("ENV", "local")  # 'local' or 'prod'
    
    # Model Paths (Local)
    FAST_MODEL_PATH: str = str(BASE_DIR / "models" / "clinical_text_classifier.pkl")
    VECTORIZER_PATH: str = str(BASE_DIR / "models" / "tfidf_vectorizer.pkl")
    TRANSFORMER_MODEL_PATH: str = str(BASE_DIR / "models" / "distilbert")
    
    # Remote Hugging Face Model Repository
    HF_MODEL_REPO_ID: str = "abhshkgtm19/Healthcare-NLP-Models"
    
    # Pre-trained Transformer configurations
    HF_TRANSFORMER_MODEL_ID: str = os.getenv("HF_TRANSFORMER_MODEL_ID", "distilbert-base-uncased")
    
    # Dataset Paths
    DATA_PATH: str = str(BASE_DIR / "dataset" / "mtsamples.csv")
    
    # NLTK Path
    NLTK_DATA_PATH: str = os.getenv("NLTK_DATA", str(BASE_DIR / "nltk_data"))

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
