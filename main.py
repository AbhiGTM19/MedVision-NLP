import os
# import torch
import pickle
# import numpy as np
from flask import Flask, request, jsonify, render_template
# Use the 'Fast' version of the tokenizer
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification, pipeline
import common

app = Flask(__name__)

# --- Global Model Storage ---
models = {
    "fast": None,
    "accurate": None
}
vectorizer = None

# --- Load Models on Startup ---
def load_models():
    """Loads all models into memory."""
    global vectorizer, models
    
    # Load the fast SGDClassifier model
    try:
        with open('models/movies_review_classifier.pkl', 'rb') as f_model:
            models["fast"] = pickle.load(f_model)
        with open('models/tfidf_vectorizer.pkl', 'rb') as f_vect:
            vectorizer = pickle.load(f_vect)
        print("✅ SGDClassifier model loaded successfully!")
    except FileNotFoundError:
        print("🔴 Warning: SGDClassifier model files not found. The 'fast' option will be unavailable.")

    # Load the accurate DistilBERT model
    try:
        distilbert_path = 'models/distilbert'
        if os.path.exists(distilbert_path):
            # Use DistilBertTokenizerFast
            tokenizer = DistilBertTokenizerFast.from_pretrained(distilbert_path)
            model = DistilBertForSequenceClassification.from_pretrained(distilbert_path)
            # Create a pipeline for easier inference
            models["accurate"] = pipeline(
                "sentiment-analysis",
                model=model,
                tokenizer=tokenizer,
                device=-1  # Use CPU for compatibility with Render's free tier
            )
            print("✅ DistilBERT model loaded successfully!")
        else:
             print("🔴 Warning: DistilBert model directory not found. The 'accurate' option will be unavailable.")
    except Exception as e:
        print(f"🔴 Error loading DistilBert model: {e}")

load_models()

# --- Home Route defined here ---
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

# --- Health Check Endpoint defined here ---
@app.route("/health", methods=["GET"])
def health_check():
    import os
    import nltk

    # Ensure NLTK can find data
    nltk_path = os.getenv("NLTK_DATA", os.path.expanduser("~/nltk_data"))
    nltk.data.path.append(nltk_path)

    try:
        nltk.corpus.stopwords.words("english")
        nltk.data.find("tokenizers/punkt")
        nltk_ok = True
    except Exception as e:
        print("🔴 NLTK Error:", e)
        nltk_ok = False

    from utils import load_pickle_safe, load_transformer_safe
    models_status = {
        "fast_model": os.path.exists("models/movies_review_classifier.pkl"),
        "tfidf_vectorizer": os.path.exists("models/tfidf_vectorizer.pkl"),
        "transformer_model": os.path.exists("models/distilbert/"),
    }

    overall_status = (
        "ok" if all(models_status.values()) and nltk_ok else "degraded"
    )

    return jsonify({
        "status": overall_status,
        "models": models_status,
        "nltk_data": nltk_ok
    }), 200

# --- Model Info Endpoint defined here ---
@app.route("/model-info", methods=["GET"])
def model_info():
    model_choice = request.args.get('model', 'fast')
    if models.get(model_choice):
        if model_choice == 'fast':
            return jsonify(models['fast'].get_params())
        else:
            # For DistilBERT, we can return its configuration
            return jsonify(models['accurate'].model.config.to_dict())
    return jsonify({"error": f"Model '{model_choice}' not loaded"}), 500

# --- Predict Endpoint defined here ---
@app.route("/predict", methods=["POST"])
def predict_review():
    data = request.get_json()
    movie_review = data.get("review")
    model_choice = data.get("model_choice", "fast")

    if not movie_review:
        return jsonify({"error": "Review text is missing."}), 400
    
    selected_model = models.get(model_choice)
    if not selected_model:
        return jsonify({"error": f"Model '{model_choice}' is not available for prediction."}), 500

    if model_choice == "fast":
        # --- Fast Model Prediction (SGDClassifier) ---
        preprocessed_review = common.preprocess_text(movie_review)
        new_review_tfidf = vectorizer.transform([preprocessed_review])
        
        prediction_val = selected_model.predict(new_review_tfidf)[0]
        proba = selected_model.predict_proba(new_review_tfidf)[0]
        confidence = max(proba)
        
        prediction_label = "positive" if prediction_val == 1 else "negative"
        
        # Get word importances
        feature_names = vectorizer.get_feature_names_out()
        coef = selected_model.coef_[0]
        word_coef_map = {word: coef_val for word, coef_val in zip(feature_names, coef)}
        present_words = preprocessed_review.split()
        word_importances = {word: word_coef_map.get(word, 0) for word in present_words if word in word_coef_map}

    else:
        # --- Accurate Model Prediction (DistilBERT) ---
        # The pipeline returns a list with a dictionary, e.g., [{'label': 'LABEL_1', 'score': 0.99...}]
        result = selected_model(movie_review)[0]
        prediction_label = "positive" if result['label'] == 'LABEL_1' else "negative"
        confidence = result['score']
        word_importances = {} # Word importance is not easily available for transformers without more complex libraries (LIME/SHAP)

    verdict = "Recommended ✅" if prediction_label == "positive" else "Not Recommended ❌"

    return jsonify({
        "prediction": prediction_label,
        "confidence": confidence,
        "verdict": verdict,
        "word_importances": word_importances,
        "model_used": model_choice
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)