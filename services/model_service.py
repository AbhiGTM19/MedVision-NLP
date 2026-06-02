import logging
import os
import pickle
from typing import Dict, Tuple

from transformers import DistilBertForSequenceClassification, DistilBertTokenizerFast, pipeline

import common
from core.config import settings

logger = logging.getLogger(__name__)

class ModelService:
    def __init__(self):
        self.fast_model = None
        self.vectorizer = None
        self.accurate_pipeline = None
        self._load_models()

    def _load_models(self):
        # Load fast model
        try:
            if os.path.exists(settings.FAST_MODEL_PATH) and os.path.exists(settings.VECTORIZER_PATH):
                with open(settings.FAST_MODEL_PATH, 'rb') as f_model:
                    self.fast_model = pickle.load(f_model)
                with open(settings.VECTORIZER_PATH, 'rb') as f_vect:
                    self.vectorizer = pickle.load(f_vect)
                logger.info("✅ SGDClassifier model loaded successfully!")
            else:
                logger.warning("🔴 Fast model files not found.")
        except Exception as e:
            logger.error(f"Error loading fast model: {e}")

        # Load accurate model
        try:
            # If in prod and HF_TRANSFORMER_MODEL_ID is set, download directly from Hugging Face Hub
            model_path = settings.TRANSFORMER_MODEL_PATH
            if settings.ENV == "prod" and settings.HF_TRANSFORMER_MODEL_ID:
                model_path = settings.HF_TRANSFORMER_MODEL_ID
                logger.info(f"Downloading DistilBERT from Hugging Face Hub: {model_path}")
            
            if settings.ENV == "prod" and settings.HF_TRANSFORMER_MODEL_ID or os.path.exists(settings.TRANSFORMER_MODEL_PATH):
                tokenizer = DistilBertTokenizerFast.from_pretrained(model_path)
                model = DistilBertForSequenceClassification.from_pretrained(model_path)
                self.accurate_pipeline = pipeline(
                    "sentiment-analysis",
                    model=model,
                    tokenizer=tokenizer,
                    device=-1,
                    truncation=True,
                    max_length=512
                )
                logger.info("✅ DistilBERT model loaded successfully!")
            else:
                logger.warning("🔴 DistilBert model directory not found.")
        except Exception as e:
            logger.error(f"Error loading DistilBert model: {e}")

    def is_fast_ready(self) -> bool:
        return self.fast_model is not None and self.vectorizer is not None

    def is_accurate_ready(self) -> bool:
        return self.accurate_pipeline is not None

    def predict_fast(self, review: str) -> Tuple[str, float, Dict[str, float]]:
        if not self.is_fast_ready():
            raise ValueError("Fast model is not loaded.")
        
        preprocessed_review = common.preprocess_text(review)
        new_review_tfidf = self.vectorizer.transform([preprocessed_review])
        
        prediction_val = self.fast_model.predict(new_review_tfidf)[0]
        proba = self.fast_model.predict_proba(new_review_tfidf)[0]
        confidence = max(proba)
        prediction_label = "positive" if prediction_val == 1 else "negative"
        
        feature_names = self.vectorizer.get_feature_names_out()
        coef = self.fast_model.coef_[0]
        word_coef_map = {word: coef_val for word, coef_val in zip(feature_names, coef)}
        present_words = preprocessed_review.split()
        word_importances = {word: word_coef_map.get(word, 0) for word in present_words if word in word_coef_map}
        
        return prediction_label, confidence, word_importances

    def predict_accurate(self, review: str) -> Tuple[str, float, Dict[str, float]]:
        if not self.is_accurate_ready():
            raise ValueError("Accurate model is not loaded.")
        
        result = self.accurate_pipeline(review)[0]
        prediction_label = "positive" if result['label'] == 'LABEL_1' else "negative"
        confidence = result['score']
        
        # Surrogate explainability: Use the linear fast model to generate word weights for the UI
        word_importances = {}
        if self.is_fast_ready():
            _, _, word_importances = self.predict_fast(review)
            
        return prediction_label, confidence, word_importances

# Singleton instance
model_service = ModelService()
