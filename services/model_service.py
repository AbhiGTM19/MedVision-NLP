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
            if os.path.exists(settings.TRANSFORMER_MODEL_PATH):
                tokenizer = DistilBertTokenizerFast.from_pretrained(settings.TRANSFORMER_MODEL_PATH)
                model = DistilBertForSequenceClassification.from_pretrained(settings.TRANSFORMER_MODEL_PATH)
                self.accurate_pipeline = pipeline(
                    "sentiment-analysis",
                    model=model,
                    tokenizer=tokenizer,
                    device=-1
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
        return prediction_label, confidence, {}

# Singleton instance
model_service = ModelService()
