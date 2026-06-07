"""Evaluate both fast (SGDClassifier) and transformer models on the clinical notes dataset."""
import os
import time

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

# Suppress Hugging Face warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from core.config import settings
from services.model_service import model_service


def load_test_data(sample_size: int = 200) -> tuple[list[str], list[str]]:
    """Load a random sample of clinical notes from the CSV dataset for evaluation."""
    df = pd.read_csv(settings.DATA_PATH)
    df = df.dropna(subset=["transcription", "medical_specialty"])

    _, test_df = train_test_split(df, test_size=0.2, random_state=42)
    test_df = test_df.sample(n=min(sample_size, len(test_df)), random_state=42)

    return test_df["transcription"].tolist(), test_df["medical_specialty"].tolist()


def evaluate_models() -> None:
    texts, true_labels = load_test_data(sample_size=200)
    if not texts:
        print("Error: No test data loaded.")
        return

    print(f"Evaluating on {len(texts)} clinical notes...\n")

    # --- Fast Model (SGDClassifier) ---
    print("Evaluating Fast Model (SGDClassifier)...")
    fast_preds: list[str] = []
    fast_start = time.time()
    for text in texts:
        label, _, _ = model_service.predict_fast(text)
        fast_preds.append(label)
    fast_end = time.time()

    # --- Transformer Model (DistilBERT) ---
    print("Evaluating Deep Transformer (DistilBERT)...")
    accurate_preds: list[str] = []
    acc_start = time.time()
    for text in texts:
        label, _, _ = model_service.predict_accurate(text)
        accurate_preds.append(label)
    acc_end = time.time()

    # --- Metrics ---
    fast_acc = accuracy_score(true_labels, fast_preds)
    fast_latency = (fast_end - fast_start) / len(texts) * 1000

    acc_acc = accuracy_score(true_labels, accurate_preds)
    acc_latency = (acc_end - acc_start) / len(texts) * 1000

    print("\n" + "=" * 50)
    print("🚀 FAST MODEL (SGDClassifier) METRICS")
    print("=" * 50)
    print(f"Accuracy:  {fast_acc * 100:.2f}%")
    print(f"Latency:   {fast_latency:.2f} ms/sample")
    print("\nClassification Report:")
    print(classification_report(true_labels, fast_preds, zero_division=0))

    print("\n" + "=" * 50)
    print("🧠 DEEP TRANSFORMER (DistilBERT) METRICS")
    print("=" * 50)
    print(f"Accuracy:  {acc_acc * 100:.2f}%")
    print(f"Latency:   {acc_latency:.2f} ms/sample")
    print("\nClassification Report:")
    print(classification_report(true_labels, accurate_preds, zero_division=0))
    print("=" * 50)


if __name__ == "__main__":
    evaluate_models()
