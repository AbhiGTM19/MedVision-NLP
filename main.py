from flask import Flask, request, jsonify
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
import common
import mlflow

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route("/", methods=["GET"])
def home():
    return "Welcome to the Movie Review Classifier!"

@app.route("/predict", methods=["POST"])
def predict_review():
    data = request.get_json()
    movie_review = data.get("review")
    
    # Load vectorizer and model
    with open('models/tfidf_vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
    
    preprocessed_review = common.preprocess_text(movie_review)
    new_review_tfidf = vectorizer.transform([preprocessed_review])

    with open("models/movies_review_classifier.pkl", "rb") as f:
        model = pickle.load(f)
    
    prediction = model.predict(new_review_tfidf)[0]
    return jsonify({"prediction": str(prediction)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)