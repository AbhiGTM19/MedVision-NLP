import string
from tokenize import String

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
    global op
    with open('models/movies_review_classifier.pkl', 'rb') as file:
        model = pickle.load(file)
    params=""
    if hasattr(model, 'best_params_'):
        print("Best Model Parameters:")
        for param, value in model.best_params_.items():
            print(f"{param}: {value}")
        print(f"Best Score: {model.best_score_:.4f}")
    else:
        print("No hyperparameter search found. Printing all model parameters:")
        params = model.get_params()
        op=""
        for param, value in params.items():
            op+=param+":"+str(value)+","
            #print(f"{param}: {value}")
        print(f"{op}")
    return params

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