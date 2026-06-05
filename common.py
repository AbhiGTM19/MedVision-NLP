import os
import re

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Ensure NLTK can find the downloaded data locally in the project directory
project_root = os.path.dirname(os.path.abspath(__file__))
nltk_local_path = os.path.join(project_root, "nltk_data")

# Override NLTK data paths to look strictly in our project directory (or custom NLTK_DATA env var)
nltk.data.path = [os.getenv("NLTK_DATA", nltk_local_path)]

print("📂 Current NLTK paths:", nltk.data.path)
if os.path.exists(nltk.data.path[0]):
    print("📁 Available files in NLTK path:", os.listdir(nltk.data.path[0]))
else:
    print("⚠️ NLTK path does not exist:", nltk.data.path[0])


def preprocess_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]
    return ' '.join(tokens)
