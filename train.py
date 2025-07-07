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
import mlflow
import mlflow.sklearn
import optuna
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

def objective(trial, X_train, X_test, y_train, y_test):
    kernel = trial.suggest_categorical("kernel", ["linear", "rbf"])
    C = trial.suggest_loguniform("C", 1e-3, 100)
    gamma = trial.suggest_loguniform("gamma", 1e-4, 1.0) if kernel == "rbf" else "scale"

    model = SVC(C=C, kernel=kernel, gamma=gamma, probability=True)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    accuracy = accuracy_score(y_test, preds)
    return accuracy

def train_model():
    start = time.time()
    print("1. Loading and preprocessing")
    pos_path = "aclImdb/train/pos"
    neg_path = "aclImdb/train/neg"
    df = load_data(pos_path, neg_path)
    df['processed_review'] = df['review'].apply(common.preprocess_text)

    print("2. Splitting")
    X_train_text, X_test_text, y_train, y_test = train_test_split(
        df['processed_review'], df['sentiment'], test_size=0.2, random_state=42)

    print("3. TF-IDF Vectorizing")
    vectorizer = TfidfVectorizer(max_features=5000)
    X_train = vectorizer.fit_transform(X_train_text)
    X_test = vectorizer.transform(X_test_text)

    print("4. Starting Optuna Tuning...")
    study = optuna.create_study(direction="maximize")
    study.optimize(lambda trial: objective(trial, X_train, X_test, y_train, y_test), n_trials=25)

    print("5. Best params:", study.best_params)

    best_kernel = study.best_params["kernel"]
    best_C = study.best_params["C"]
    best_gamma = study.best_params.get("gamma", "scale")

    best_model = SVC(C=best_C, kernel=best_kernel, gamma=best_gamma, probability=True)
    best_model.fit(X_train, y_train)
    y_pred = best_model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    mlflow.set_experiment("Movie_Review_Classifier_Optuna")
    with mlflow.start_run():
        mlflow.log_params(study.best_params)
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("f1_score", f1)

        # Save models
        os.makedirs("models", exist_ok=True)
        pickle.dump(vectorizer, open("models/tfidf_vectorizer.pkl", "wb"))
        pickle.dump(best_model, open("models/movies_review_classifier.pkl", "wb"))
        mlflow.log_artifacts("models")

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

        # Top TF-IDF features (only for linear kernel)
        if best_kernel == "linear":
            coef = best_model.coef_[0]
            feature_names = vectorizer.get_feature_names_out()
            top_indices = coef.argsort()[-10:][::-1]
            top_features = [(feature_names[i], round(coef[i], 4)) for i in top_indices]
            with open("top_features.csv", "w") as f:
                f.write("feature,weight\n")
                for word, weight in top_features:
                    f.write(f"{word},{weight}\n")
            mlflow.log_artifact("top_features.csv")

        mlflow.sklearn.log_model(best_model, "svc_model")

    print(f"✔️ Training Done | Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
    print(f"🕒 Total Time: {time.time() - start:.2f} sec")

if __name__ == "__main__":
    train_model()
