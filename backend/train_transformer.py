"""Fine-tune DistilBERT on the MTSamples medical transcription dataset for multi-class specialty classification."""
import os

import evaluate
import mlflow
import numpy as np

from core.config import BASE_DIR

# Fix for the URL-encoding bug that creates "AI%20ML" directories
os.makedirs(BASE_DIR / "mlruns", exist_ok=True)
mlflow.set_tracking_uri(f"sqlite:///{BASE_DIR}/mlruns/mlflow.db")

import pandas as pd
from datasets import Dataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from transformers import (
    DistilBertForSequenceClassification,
    DistilBertTokenizerFast,
    Trainer,
    TrainingArguments,
)

from core.config import settings


def load_clinical_data(data_path: str) -> pd.DataFrame:
    """Loads clinical notes from the CSV dataset and prepares labels."""
    df = pd.read_csv(data_path)
    df = df.dropna(subset=["transcription", "medical_specialty"])

    # Filter to top-N specialties to keep training feasible
    top_specialties = df["medical_specialty"].value_counts().head(10).index.tolist()
    df = df[df["medical_specialty"].isin(top_specialties)].reset_index(drop=True)

    return df


def main() -> None:
    """Main function to fine-tune and save the DistilBERT model for clinical text classification."""
    import transformers
    transformers.logging.set_verbosity_error()
    print("--- Starting DistilBERT Fine-Tuning (Healthcare) ---")

    print("1. Loading clinical notes dataset...")
    df = load_clinical_data(settings.DATA_PATH)

    # Encode string labels to integers for the Trainer
    label_encoder = LabelEncoder()
    df["label"] = label_encoder.fit_transform(df["medical_specialty"])
    num_labels = len(label_encoder.classes_)
    print(f"   Found {len(df)} samples across {num_labels} specialties: {list(label_encoder.classes_)}")

    # Save label mapping for inference
    label_map = {int(i): label for i, label in enumerate(label_encoder.classes_)}

    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df["label"])

    train_dataset = Dataset.from_pandas(train_df[["transcription", "label"]].rename(columns={"transcription": "text"}))
    val_dataset = Dataset.from_pandas(val_df[["transcription", "label"]].rename(columns={"transcription": "text"}))

    print("2. Tokenizing data...")
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")

    def tokenize_function(examples: dict) -> dict:
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=256)

    train_dataset = train_dataset.map(tokenize_function, batched=True)
    val_dataset = val_dataset.map(tokenize_function, batched=True)

    train_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
    val_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])

    print(f"3. Loading pre-trained DistilBERT model (num_labels={num_labels})...")
    model = DistilBertForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=num_labels)

    training_args = TrainingArguments(
        output_dir="./results",
        num_train_epochs=3,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        warmup_steps=200,
        weight_decay=0.01,
        logging_dir="./logs",
        logging_steps=50,
        eval_strategy="steps",
        eval_steps=200,
        save_strategy="steps",
        save_steps=200,
        load_best_model_at_end=True,
    )

    metric = evaluate.load("accuracy")

    def compute_metrics(eval_pred: tuple) -> dict:
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        return metric.compute(predictions=predictions, references=labels)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
    )

    mlflow.set_experiment("Healthcare_DistilBERT_Fine_Tuning")

    print("4. Fine-tuning the model...")
    trainer.train()

    output_model_dir = settings.TRANSFORMER_MODEL_PATH
    os.makedirs(output_model_dir, exist_ok=True)
    print(f"5. Saving fine-tuned model and tokenizer to {output_model_dir}...")

    model.save_pretrained(output_model_dir)
    tokenizer.save_pretrained(output_model_dir)

    # Save label map alongside the model
    import json
    with open(os.path.join(output_model_dir, "label_map.json"), "w") as f:
        json.dump(label_map, f, indent=2)

    print("--- DistilBERT Healthcare Fine-Tuning Complete ---")


if __name__ == "__main__":
    main()