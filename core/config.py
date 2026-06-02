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
    
    # Remote Hugging Face Model Repository
    HF_MODEL_REPO_ID: str = "abhshkgtm19/Movie-Review-Sentiment-Models"
    
    # Pre-trained Transformer configurations
    HF_TRANSFORMER_MODEL_ID: str = os.getenv("HF_TRANSFORMER_MODEL_ID", "distilbert-base-uncased-finetuned-sst-2-english")
    
    # Dataset Paths
    POS_DATA_PATH: str = "dataset/aclImdb/train/pos"
    NEG_DATA_PATH: str = "dataset/aclImdb/train/neg"
    
    # NLTK Path
    NLTK_DATA_PATH: str = os.getenv("NLTK_DATA", os.path.expanduser("~/nltk_data"))

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
