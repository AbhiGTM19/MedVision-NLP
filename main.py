from flask import Flask, request, jsonify, render_template # type: ignore
import pickle
import os
import common

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/model-info", methods=["GET"])
def model_info():
    with open('models/movies_review_classifier.pkl', 'rb') as file:
        model = pickle.load(file)

    if hasattr(model, 'best_params_'):
        best_params = model.best_params_
        best_score = model.best_score_
        return jsonify({
            "best_params": best_params,
            "best_score": round(best_score, 4)
        })
    else:
        all_params = model.get_params()
        return jsonify(all_params)

@app.route("/predict", methods=["POST"])
def predict_review():
    data = request.get_json()
    movie_review = data.get("review")

    with open('models/movies_review_classifier.pkl', 'rb') as file:
        model = pickle.load(file)
    with open('models/tfidf_vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)

    preprocessed_review = common.preprocess_text(movie_review)
    new_review_tfidf = vectorizer.transform([preprocessed_review])

    prediction = model.predict(new_review_tfidf)[0]
    proba = model.predict_proba(new_review_tfidf)[0]
    confidence = max(proba)

    sentiment_label = "positive" if prediction == 1 else "negative"
    verdict = "Recommended ✅" if prediction == 1 else "Not Recommended ❌"
    star_rating = "⭐⭐⭐⭐" if prediction == 1 else "⭐"

    feature_names = vectorizer.get_feature_names_out()
    tfidf_scores = new_review_tfidf.toarray()[0]
    top_indices = tfidf_scores.argsort()[-5:][::-1]
    top_words = [feature_names[i] for i in top_indices if tfidf_scores[i] > 0]

    return jsonify({
        "prediction": sentiment_label,
        "confidence": round(confidence, 4),
        "verdict": verdict,
        "rating": star_rating,
        "top_words": top_words
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
