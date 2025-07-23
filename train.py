import os
import time
import pickle
import pandas as pd # type: ignore
import matplotlib.pyplot as plt # type: ignore
import seaborn as sns # type: ignore
from sklearn.model_selection import train_test_split # type: ignore
from sklearn.feature_extraction.text import TfidfVectorizer # type: ignore
from sklearn.linear_model import SGDClassifier # type: ignore
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix # type: ignore
import mlflow # type: ignore
import mlflow.sklearn # type: ignore
import optuna # type: ignore
import common

def load_data(pos_path, neg_path):
    """Loads positive and negative review data from specified paths."""
    pos_files = [os.path.join(pos_path, f) for f in os.listdir(pos_path) if f.endswith('.txt')]
    pos_reviews = [open(f, 'r', encoding='utf-8').read() for f in pos_files]
    neg_files = [os.path.join(neg_path, f) for f in os.listdir(neg_path) if f.endswith('.txt')]
    neg_reviews = [open(f, 'r', encoding='utf-8').read() for f in neg_files]

    df = pd.DataFrame({
        'review': pos_reviews + neg_reviews,
        'sentiment': [1] * len(pos_reviews) + [0] * len(neg_reviews)
    })
    return df

def objective(trial, X_train, X_test, y_train, y_test):
    """Defines the Optuna objective function for hyperparameter tuning."""
    alpha = trial.suggest_float("alpha", 1e-5, 1e-1, log=True)
    
    model = SGDClassifier(
        # Use 'log' which is the correct name for logistic regression loss in this scikit-learn version
        loss='log',  
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
    pos_path = "aclImdb/train/pos"
    neg_path = "aclImdb/train/neg"
    df = load_data(pos_path, neg_path)
    df['processed_review'] = df['review'].apply(common.preprocess_text)

    print("2. Splitting data...")
    X_train_text, X_test_text, y_train, y_test = train_test_split(
        df['processed_review'], df['sentiment'], test_size=0.2, random_state=42
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
        # Use 'log' here as well for the final model
        loss='log',
        penalty='l2',
        alpha=study.best_params['alpha'],
        random_state=42,
        max_iter=1000,
        tol=1e-3
    )
    best_model.fit(X_train, y_train)
    y_pred = best_model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    mlflow.set_experiment("Movie_Review_Classifier_Optuna_SGD")
    with mlflow.start_run():
        mlflow.log_params(study.best_params)
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("f1_score", f1)

        os.makedirs("models", exist_ok=True)
        with open("models/tfidf_vectorizer.pkl", "wb") as f:
            pickle.dump(vectorizer, f)
        with open("models/movies_review_classifier.pkl", "wb") as f:
            pickle.dump(best_model, f)
        mlflow.log_artifacts("models")

        cm = confusion_matrix(y_test, y_pred)
        plt.figure(figsize=(6, 4))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["neg", "pos"], yticklabels=["neg", "pos"])
        plt.xlabel("Predicted")
        plt.ylabel("Actual")
        plt.title("Confusion Matrix")
        plt.tight_layout()
        plt.savefig("confusion_matrix.png")
        mlflow.log_artifact("confusion_matrix.png")

        coef = best_model.coef_[0]
        feature_names = vectorizer.get_feature_names_out()
        top_indices = coef.argsort()[-10:][::-1]
        top_features = [(feature_names[i], round(coef[i], 4)) for i in top_indices]
        with open("top_features.csv", "w") as f:
            f.write("feature,weight\n")
            for word, weight in top_features:
                f.write(f"{word},{weight}\n")
        mlflow.log_artifact("top_features.csv")

        mlflow.sklearn.log_model(best_model, "sgd_classifier_model")

    print(f"✔️ Training Done | Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
    print(f"🕒 Total Time: {time.time() - start:.2f} sec")

if __name__ == "__main__":
    train_model()