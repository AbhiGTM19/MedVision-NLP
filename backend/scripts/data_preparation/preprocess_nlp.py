import os
import pandas as pd
import re
import nltk
from pathlib import Path
from tqdm import tqdm
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

def clean_text(text):
    if not isinstance(text, str):
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Very basic PHI scrubbing using Regex
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]', text)
    text = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE_REDACTED]', text)
    text = re.sub(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', '[DATE_REDACTED]', text)
    
    # Remove special characters but keep spaces and alphanumeric
    text = re.sub(r'[^a-z0-9\s\[\]\_]', ' ', text)
    
    tokens = text.split()
    stop_words = set(stopwords.words('english'))
    
    # Retain domain-specific logic if needed, but remove general stop words
    tokens = [word for word in tokens if word not in stop_words]
    
    # Lemmatize
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    
    return " ".join(tokens)

def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    raw_dir = base_dir / "dataset" / "raw"
    processed_dir = base_dir / "dataset" / "processed" / "nlp_text"
    
    os.makedirs(processed_dir, exist_ok=True)
    
    csv_files = list(raw_dir.rglob("*.csv"))
    print(f"Found {len(csv_files)} CSV files for NLP preprocessing.")
    
    for csv_file in csv_files:
        print(f"Processing {csv_file.name}...")
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            print(f"Could not read {csv_file.name}: {e}")
            continue
        
        # Look for typical text columns
        text_cols = [c for c in df.columns if 'text' in c.lower() or 'transcription' in c.lower() or 'note' in c.lower()]
        if not text_cols:
            print(f"No obvious text columns found in {csv_file.name}. Skipping.")
            continue
            
        target_col = text_cols[0]
        tqdm.pandas(desc=f"Cleaning {target_col}")
        df[f"cleaned_{target_col}"] = df[target_col].progress_apply(clean_text)
        
        save_path = processed_dir / f"cleaned_{csv_file.name}"
        df.to_csv(save_path, index=False)
        print(f"Saved cleaned data to {save_path}")

if __name__ == "__main__":
    main()
