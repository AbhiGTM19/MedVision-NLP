import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Sentiment Scope API"
    VERSION: str = "1.0.0"
    ENV: str = os.getenv("ENV", "local")  # 'local' or 'prod'
    
    # Model Paths (Local)
    FAST_MODEL_PATH: str = "models/movies_review_classifier.pkl"
    VECTORIZER_PATH: str = "models/tfidf_vectorizer.pkl"
    TRANSFORMER_MODEL_PATH: str = "models/distilbert"
    
    # Hugging Face Hub (Production)
    HF_TRANSFORMER_MODEL_ID: str = os.getenv("HF_TRANSFORMER_MODEL_ID", "")
    
    # Dataset Paths
    POS_DATA_PATH: str = "dataset/aclImdb/train/pos"
    NEG_DATA_PATH: str = "dataset/aclImdb/train/neg"
    
    # NLTK Path
    NLTK_DATA_PATH: str = os.getenv("NLTK_DATA", os.path.expanduser("~/nltk_data"))

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
