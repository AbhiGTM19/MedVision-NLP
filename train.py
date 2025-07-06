import os
import time
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from skopt import BayesSearchCV
from skopt.space import Real, Categorical

import mlflow
import mlflow.sklearn
import common

def load_data(pos_path, neg_path):
    pos_files = [os.path.join(pos_path, f) for f in os.listdir(pos_path) if f.endswith('.txt')]
    pos_reviews = [open(f, 'r', encoding='utf-8').read() for f in pos_files]
    neg_files = [os.path.join(neg_path, f) for f in os.listdir(neg_path) if f.endswith('.txt')]
    neg_reviews = [open(f, 'r', encoding='utf-8').read() for f in neg_files]

    df = pd.DataFrame({
        'review': pos_reviews + neg_reviews,
        'sentiment': [1]*len(pos_reviews) + [0]*len(neg_reviews)
    })
    return df

def train_model():
    start = time.time()

    print("1. Loading and preprocessing")
    pos_path = "aclImdb/train/pos"
    neg_path = "aclImdb/train/neg"
    df = load_data(pos_path, neg_path)
    df['processed_review'] = df['review'].apply(common.preprocess_text)

    print("2. Splitting")
    X_train, X_test, y_train, y_test = train_test_split(
        df['processed_review'], df['sentiment'], test_size=0.2, random_state=42)

    print("3. TF-IDF Vectorizing")
    vectorizer = TfidfVectorizer(max_features=5000)
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    print("4. Bayesian Hyperparameter Tuning")

    opt_model = BayesSearchCV(
        SVC(probability=True),
        search_spaces={
            'C': Real(1e-3, 100.0, prior='log-uniform'),
            'gamma': Real(1e-4, 1.0, prior='log-uniform'),
            'kernel': Categorical(['linear', 'rbf'])
        },
        scoring='accuracy',
        n_iter=25,
        cv=3,
        n_jobs=-1,
        verbose=1,
        random_state=42
    )

    mlflow.set_experiment("Movie_Review_Classifier_Bayes")
    with mlflow.start_run():
        opt_model.fit(X_train_tfidf, y_train)
        best_model = opt_model.best_estimator_

        print(f"Best Parameters: {opt_model.best_params_}")
        mlflow.log_params(opt_model.best_params_)

        y_pred = best_model.predict(X_test_tfidf)
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)

        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("f1_score", f1)

        # Save model artifacts
        if not os.path.exists("models"):
            os.makedirs("models")
        pickle.dump(vectorizer, open("models/tfidf_vectorizer.pkl", "wb"))
        pickle.dump(best_model, open("models/movies_review_classifier.pkl", "wb"))

        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred)
        plt.figure(figsize=(6, 4))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["neg", "pos"], yticklabels=["neg", "pos"])
        plt.xlabel("Predicted")
        plt.ylabel("Actual")
        plt.title("Confusion Matrix")
        plt.tight_layout()
        plt.savefig("confusion_matrix.png")
        mlflow.log_artifact("confusion_matrix.png")

        # Top features (only for linear kernel)
        if opt_model.best_params_["kernel"] == "linear":
            coef = best_model.coef_[0]
            feature_names = vectorizer.get_feature_names_out()
            top_indices = coef.argsort()[-10:][::-1]
            top_features = [(feature_names[i], round(coef[i], 4)) for i in top_indices]
            with open("top_features.csv", "w") as f:
                f.write("feature,weight\n")
                for word, weight in top_features:
                    f.write(f"{word},{weight}\n")
            mlflow.log_artifact("top_features.csv")

        # Log model and artifacts
        mlflow.log_artifacts("models")
        mlflow.sklearn.log_model(best_model, "svc_model")

        print("Training complete.")
        print(f"Accuracy: {accuracy:.4f} | F1 Score: {f1:.4f}")
        print(f"Time taken: {time.time() - start:.2f} seconds")

if __name__ == "__main__":
    train_model()
