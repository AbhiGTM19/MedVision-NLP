# 🎬 MLOps Final Assignment — Movie Review Classification

This project is part of an MLOps final assignment focused on building, tuning, and deploying a sentiment classifier for movie reviews. It uses **NLP preprocessing**, **SVM** model tuning via **Optuna**, and tracks all artifacts via **MLflow**. A Flask API is served for prediction.

---

## 🔧 Features

- ✅ Movie Review Classifier using Scikit-learn + SVM
- ✅ Bayesian/Optuna-based hyperparameter tuning
- ✅ Preprocessing with NLTK (stopwords, tokenization, lowercase, punctuation removal)
- ✅ TF-IDF vectorization
- ✅ MLflow integration for experiment tracking
- ✅ Confusion Matrix & Top Feature logging
- ✅ REST API using Flask
- ✅ Docker-ready

---

## 📁 Project Structure

```bash
.
├── aclImdb/                     # Dataset (IMDB reviews)
│   └── train/pos, train/neg     # Positive/Negative review .txt files
├── models/                      # Saved model & vectorizer
│   ├── movies_review_classifier.pkl
│   └── tfidf_vectorizer.pkl
├── train.py                     # Training & MLflow logging
├── main.py                      # Flask API
├── common.py                    # Text preprocessing function
├── requirements.txt             # Python dependencies
└── README.md

-- CLone the Repository
git clone <your-repo-url>
cd mlops_finalassignment

-- Create Virtual Environment
python3 -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows

-- Install Dependencies
pip install -r requirements.txt

-- Download NLTK Resources (once)
python
>>> import nltk
>>> nltk.download('punkt')
>>> nltk.download('stopwords')
>>> exit()

-- Train the Model
python train.py

Artifacts logged:
Best parameters (C, kernel, gamma)
Accuracy and F1 score
Confusion matrix plot
Top TF-IDF features (if linear kernel)
Model: movies_review_classifier.pkl
Vectorizer: tfidf_vectorizer.pkl

--  Run the Flask API
flask run
Server will start at: http://127.0.0.1:5000

-- API Endpoints
1. GET /
Returns hyperparameters of trained model:
{
    "C": 10.55213024921588,
    "break_ties": false,
    "cache_size": 200,
    "class_weight": null,
    "coef0": 0.0,
    "decision_function_shape": "ovr",
    "degree": 3,
    "gamma": 0.9722301867133281,
    "kernel": "rbf",
    "max_iter": -1,
    "probability": true,
    "random_state": null,
    "shrinking": true,
    "tol": 0.001,
    "verbose": false
}

2. POST /predict
Input JSON:
{
  "review": "The movie was outstanding with powerful performances."
}

Response:
{
    "confidence": 0.9944,
    "prediction": "positive",
    "rating": "⭐⭐⭐⭐",
    "top_words": [
        "outstanding",
        "powerful",
        "performances",
        "movie"
    ],
    "verdict": "Recommended ✅"
}

-- View MLflow UI
mlflow ui
Visit: http://127.0.0.1:5000 for dashboard.

## Run with Docker (Online Method)

If you have Docker installed, pull and run directly from Docker Hub:

```bash
docker pull yugandhar0458/mlops_team10:latest
docker run -p 5000:5000 yugandhar0458/mlops_team10:latest


Authors
Team 10 — M.Tech Applied AI (MLOps)
Model tuning by: Optuna
Deployment: Flask + Docker