import matplotlib

# Set the backend to 'Agg' BEFORE importing pyplot
# This is the crucial fix for running in a headless Docker environment
matplotlib.use('Agg')

import os
import pickle
import time

import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import optuna

from core.config import BASE_DIR

# Fix for the URL-encoding bug that creates "AI%20ML" directories
os.makedirs(BASE_DIR / "mlruns", exist_ok=True)
mlflow.set_tracking_uri(f"sqlite:///{BASE_DIR}/mlruns/mlflow.db")

import pandas as pd
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split

import sys
from pathlib import Path

# Ensure backend root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core import common
from core.config import BASE_DIR, settings


def load_data(data_path):
    """Loads clinical notes data from csv."""
    df = pd.read_csv(data_path)
    df = df.dropna(subset=["transcription", "medical_specialty"])
    # Filter to top-10 specialties to keep training feasible and balanced
    top_specialties = df["medical_specialty"].value_counts().head(10).index.tolist()
    df = df[df["medical_specialty"].isin(top_specialties)].reset_index(drop=True)
    return df

def objective(trial, X_train, X_test, y_train, y_test):
    """Defines the Optuna objective function for hyperparameter tuning."""
    alpha = trial.suggest_float("alpha", 1e-5, 1e-1, log=True)
    
    model = SGDClassifier(
        loss='log_loss',  # Use 'log_loss' for modern scikit-learn
        penalty='l2',
        alpha=alpha,
        random_state=42,
        max_iter=1000,
        tol=1e-3
    )
    
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    accuracy = accuracy_score(y_test, preds)
    return accuracy

def train_model():
    """Main function to train and evaluate the model."""
    start = time.time()
    
    print("1. Loading and preprocessing data...")
    df = load_data(settings.DATA_PATH)
    df = df.assign(processed_text=df['transcription'].apply(common.preprocess_text))

    print("2. Splitting data...")
    X_train_text, X_test_text, y_train, y_test = train_test_split(
        df['processed_text'], df['medical_specialty'], test_size=0.2, random_state=42
    )

    print("3. TF-IDF Vectorizing...")
    vectorizer = TfidfVectorizer(max_features=5000)
    X_train = vectorizer.fit_transform(X_train_text)
    X_test = vectorizer.transform(X_test_text)

    print("4. Starting Optuna Tuning with parallel jobs...")
    study = optuna.create_study(direction="maximize")
    study.optimize(lambda trial: objective(trial, X_train, X_test, y_train, y_test), n_trials=25, n_jobs=-1)

    print("5. Best params found:", study.best_params)
    
    best_model = SGDClassifier(
        loss='log_loss',
        penalty='l2',
        alpha=study.best_params['alpha'],
        random_state=42,
        max_iter=1000,
        tol=1e-3
    )
    best_model.fit(X_train, y_train)
    y_pred = best_model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')

    mlflow.set_experiment("MedVision_NLP_Optuna_SGD")
    with mlflow.start_run():
        mlflow.log_params(study.best_params)
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("f1_score", f1)

        metrics_path = BASE_DIR / "metrics.txt"
        with open(metrics_path, "w") as f:
            f.write(f"Accuracy: {accuracy:.4f}\n")
            f.write(f"F1 Score: {f1:.4f}\n")

        os.makedirs(os.path.dirname(settings.VECTORIZER_PATH), exist_ok=True)
        with open(settings.VECTORIZER_PATH, "wb") as f:
            pickle.dump(vectorizer, f)
        with open(settings.FAST_MODEL_PATH, "wb") as f:
            pickle.dump(best_model, f)
        mlflow.log_artifacts("models")

        cm = confusion_matrix(y_test, y_pred)
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=best_model.classes_, yticklabels=best_model.classes_)
        plt.xlabel("Predicted")
        plt.ylabel("Actual")
        plt.title("Confusion Matrix")
        plt.tight_layout()
        cm_path = BASE_DIR / "confusion_matrix.png"
        plt.savefig(cm_path)
        mlflow.log_artifact(str(cm_path))

        coef = best_model.coef_[0]
        feature_names = vectorizer.get_feature_names_out()
        top_indices = coef.argsort()[-10:][::-1]
        top_features = [(feature_names[i], round(coef[i], 4)) for i in top_indices]
        features_path = BASE_DIR / "top_features.csv"
        with open(features_path, "w") as f:
            f.write("feature,weight\n")
            for word, weight in top_features:
                f.write(f"{word},{weight}\n")
        mlflow.log_artifact(str(features_path))

        mlflow.sklearn.log_model(best_model, "sgd_classifier_model")

    print(f"✔️ Training Done | Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
    print(f"🕒 Total Time: {time.time() - start:.2f} sec")

if __name__ == "__main__":
    train_model()