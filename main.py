from flask import Flask, request, jsonify
from joblib.parallel import method
import pickle
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
import pickle
import joblib
from skopt import BayesSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer

import common
import movie_reviews_mlflow

app = Flask(__name__) # Initialize Flask app

@app.route("/", methods=["GET"])
def home():
    return "Welcome to the Venkata's Flask App!"

@app.route("/predict", methods=["POST"]) #<-- this is the controller
def iris_prediction(): # <-- this is view function
    data = request.get_json()
    movie_review = data.get("review")
    print(f'Movie Review: {movie_review}')
    # Load the saved vectorizer
    with open('models/tfidf_vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
    preprocessed_review = common.preprocess_text(movie_review)
    new_review_tfidf = vectorizer.transform([preprocessed_review])

    with open("./models/movies_review_classifier.pkl", "rb") as fileObj:
        movies_reviews_model = pickle.load(fileObj)
    review_type = movies_reviews_model.predict(new_review_tfidf)[0]
    return jsonify({"predicted_movie_review_type": review_type[0]})

if __name__ == "__main__":
    app.run(debug=True, port=8001)