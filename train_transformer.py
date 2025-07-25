import os
import torch
import pandas as pd
import numpy as np
import evaluate 
import mlflow # Import mlflow
from sklearn.model_selection import train_test_split
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset
import common

def load_raw_data(pos_path, neg_path):
    """Loads raw movie review data from text files into a pandas DataFrame."""
    pos_files = [os.path.join(pos_path, f) for f in os.listdir(pos_path) if f.endswith('.txt')]
    pos_reviews = [open(f, 'r', encoding='utf-8').read() for f in pos_files]
    neg_files = [os.path.join(neg_path, f) for f in os.listdir(neg_path) if f.endswith('.txt')]
    neg_reviews = [open(f, 'r', encoding='utf-8').read() for f in neg_files]

    df = pd.DataFrame({
        'text': pos_reviews + neg_reviews,
        'label': [1] * len(pos_reviews) + [0] * len(neg_reviews)
    })
    return df

def main():
    """Main function to fine-tune and save the DistilBERT model."""
    print("--- Starting DistilBERT Fine-Tuning ---")

    print("1. Loading raw IMDB data...")
    pos_path = "aclImdb/train/pos"
    neg_path = "aclImdb/train/neg"
    df = load_raw_data(pos_path, neg_path)
    
    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['label'])

    train_dataset = Dataset.from_pandas(train_df)
    val_dataset = Dataset.from_pandas(val_df)

    print("2. Tokenizing data...")
    tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')

    def tokenize_function(examples):
        return tokenizer(examples['text'], padding='max_length', truncation=True, max_length=256)

    train_dataset = train_dataset.map(tokenize_function, batched=True)
    val_dataset = val_dataset.map(tokenize_function, batched=True)
    
    train_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'label'])
    val_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'label'])

    print("3. Loading pre-trained DistilBERT model...")
    model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased', num_labels=2)

    training_args = TrainingArguments(
        output_dir='./results',
        num_train_epochs=1,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=100,
        evaluation_strategy="steps",
        eval_steps=500,
        save_strategy="steps",
        save_steps=500,
        load_best_model_at_end=True
    )

    metric = evaluate.load("accuracy")

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        return metric.compute(predictions=predictions, references=labels)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics
    )

    # --- THIS IS THE FIX ---
    # Explicitly set the experiment for the Trainer to use
    mlflow.set_experiment("DistilBERT_Fine_Tuning")

    print("4. Fine-tuning the model...")
    trainer.train()

    output_model_dir = './models/distilbert'
    os.makedirs(output_model_dir, exist_ok=True)
    print(f"5. Saving fine-tuned model and tokenizer to {output_model_dir}...")
    
    model.save_pretrained(output_model_dir)
    tokenizer.save_pretrained(output_model_dir)

    print("--- DistilBERT Fine-Tuning Complete ---")

if __name__ == "__main__":
    main()