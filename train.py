import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
import pickle
import common
import mlflow
from sklearn.metrics import accuracy_score
import os

def load_data(pos_path, neg_path):
    # Load positive reviews
    pos_files = [os.path.join(pos_path, f) for f in os.listdir(pos_path) if f.endswith('.txt')]
    pos_reviews = [open(f, 'r', encoding='utf-8').read() for f in pos_files]
    
    # Load negative reviews
    neg_files = [os.path.join(neg_path, f) for f in os.listdir(neg_path) if f.endswith('.txt')]
    neg_reviews = [open(f, 'r', encoding='utf-8').read() for f in neg_files]
    
    # Create DataFrame
    df = pd.DataFrame({
        'review': pos_reviews + neg_reviews,
        'sentiment': [1]*len(pos_reviews) + [0]*len(neg_reviews)
    })
    return df

def train_model():
    # Set paths - adjust these according to your data location
    pos_path = "aclImdb/train/pos"
    neg_path = "aclImdb/train/neg"
    
    # Load and preprocess data
    df = load_data(pos_path, neg_path)
    df['processed_review'] = df['review'].apply(common.preprocess_text)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        df['processed_review'], df['sentiment'], test_size=0.2, random_state=42)
    
    # Vectorize text
    vectorizer = TfidfVectorizer(max_features=5000)
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)
    
    # Train model with MLflow tracking
    with mlflow.start_run():
        model = SVC(probability=True)
        model.fit(X_train_tfidf, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test_tfidf)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Log metrics
        mlflow.log_metric("accuracy", accuracy)
        
        # Save artifacts
        if not os.path.exists("models"):
            os.makedirs("models")
            
        pickle.dump(vectorizer, open("models/tfidf_vectorizer.pkl", "wb"))
        pickle.dump(model, open("models/movies_review_classifier.pkl", "wb"))
        
        mlflow.log_artifacts("models", "models")
        
    print(f"Model trained with accuracy: {accuracy}")

if __name__ == "__main__":
    train_model()