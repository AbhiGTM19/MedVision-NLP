import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
import mlflow
import mlflow.sklearn
import pickle

import common

nltk.download('punkt_tab')
nltk.download('stopwords')

# Define paths to the directories
train_pos_dir = 'C:/Users/yugan/Desktop/VNIT Mtech/GDrive/SEM-2/MLDeployments/Final Assignment/aclImdb_v1/aclImdb/train/pos'
train_neg_dir = 'C:/Users/yugan/Desktop/VNIT Mtech/GDrive/SEM-2/MLDeployments/Final Assignment/aclImdb_v1/aclImdb/train/neg'

test_pos_dir = 'C:/Users/yugan/Desktop/VNIT Mtech/GDrive/SEM-2/MLDeployments/Final Assignment/aclImdb_v1/aclImdb/test/pos'
test_neg_dir = 'C:/Users/yugan/Desktop/VNIT Mtech/GDrive/SEM-2/MLDeployments/Final Assignment/aclImdb_v1/aclImdb/test/neg'


# Function to read reviews and assign sentiment
def load_reviews(directory, sentiment):
    reviews = []
    for filename in os.listdir(directory):
        if filename.endswith('.txt'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                review_text = file.read()
                reviews.append({'review': review_text, 'sentiment': sentiment})
    return reviews

# Load positive and negative reviews
train_pos_reviews = load_reviews(train_pos_dir, 'positive')
train_neg_reviews = load_reviews(train_neg_dir, 'negative')

test_pos_reviews = load_reviews(test_pos_dir, 'positive')
test_neg_reviews = load_reviews(test_neg_dir, 'negative')

# Combine both lists
all_train_reviews = train_pos_reviews + train_neg_reviews
all_test_reviews = test_pos_reviews + test_neg_reviews


# Create DataFrame
train_df = pd.DataFrame(all_train_reviews, columns=['review', 'sentiment'])
test_df = pd.DataFrame(all_test_reviews, columns=['review', 'sentiment'])

# Apply preprocessing to reviews
train_df['review'] = train_df['review'].apply(common.preprocess_text)

train_df.head()

X_train=train_df['review']
y_train=train_df['sentiment']

X_test=test_df['review']
y_test=test_df['sentiment']

# Convert text to TF-IDF features
vectorizer = TfidfVectorizer(max_features=5000)  # Limit to top 5000 words
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)


mlflow.set_tracking_uri("http://127.0.0.1:5000")

with mlflow.start_run():
    # Initialize and train the model
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train_tfidf, y_train)

    # Make predictions
    y_pred = model.predict(X_test_tfidf)

    # Evaluate the model
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Negative', 'Positive']))

    with open('models/movies_review_classifier.pkl', 'wb') as f:
        pickle.dump(model, f)
        print("Model creation done")

    with open('models/tfidf_vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer,f)

        mlflow.log_metric("accuracy", accuracy)
        mlflow.sklearn.log_model(model, "movie_reviews")