import os
import nltk

# Ensure NLTK can find the downloaded data
nltk_path = os.getenv("NLTK_DATA", os.path.expanduser("~/nltk_data"))
nltk.data.path.append(nltk_path)

print("📂 Current NLTK paths:", nltk.data.path)
print("📁 Available files in first path:", os.listdir(nltk.data.path[0]))


from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]
    return ' '.join(tokens)
