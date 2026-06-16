import os

import evaluate
import numpy as np
import pandas as pd
import torch
from datasets import Dataset
from transformers import (
    AutoConfig,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

BASE_DIR = "/Users/abhi/Downloads/AI ML/MedVision-NLP"
MODELS_DIR = os.path.join(BASE_DIR, "backend/models")
BERT_DIR = os.path.join(MODELS_DIR, "bio_clinicalBERT")
DATA_CSV = os.path.join(BASE_DIR, "backend/dataset/processed/tesseract_finetune_data.csv")

device = torch.device("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

def main():
    print("Loading dataset...")
    df = pd.read_csv(DATA_CSV)
    df = df.dropna(subset=['text', 'label'])
    
    # Load config to get the exact label mapping
    config = AutoConfig.from_pretrained(BERT_DIR)
    label2id = config.label2id
    
    # Filter out any labels that might not exist in the config
    df = df[df['label'].isin(label2id.keys())]
    df['labels'] = df['label'].map(label2id)
    
    # Sub-sample heavily to make local training fast
    df = df.sample(n=500, random_state=42)
    print(f"Total training samples: {len(df)}")
    
    dataset = Dataset.from_pandas(df)
    dataset = dataset.train_test_split(test_size=0.1, seed=42)
    
    print("Loading tokenizer and existing model weights...")
    tokenizer = AutoTokenizer.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")
    
    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=256)
        
    tokenized_datasets = dataset.map(tokenize_function, batched=True)
    tokenized_datasets = tokenized_datasets.remove_columns(['text', 'label', 'source'])
    if '__index_level_0__' in tokenized_datasets['train'].column_names:
        tokenized_datasets = tokenized_datasets.remove_columns(['__index_level_0__'])
    tokenized_datasets.set_format("torch")
    
    # Load the CURRENT model weights
    model = AutoModelForSequenceClassification.from_config(config)
    bert_pth_path = os.path.join(BERT_DIR, "bio_clinicalBERT_model.pth")
    if os.path.exists(bert_pth_path):
        model.load_state_dict(torch.load(bert_pth_path, map_location=device, weights_only=True))
        print("Loaded existing model weights for fine-tuning.")
    else:
        print("Warning: existing weights not found, using base model.")
        model = AutoModelForSequenceClassification.from_pretrained("emilyalsentzer/Bio_ClinicalBERT", num_labels=len(label2id), id2label=config.id2label, label2id=label2id)
    
    metric = evaluate.load("f1")
    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        return metric.compute(predictions=predictions, references=labels, average="macro")
        
    training_args = TrainingArguments(
        output_dir=os.path.join(BASE_DIR, "backend/scripts/data_preparation/bert-finetune-results"),
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=3e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=2, # Fast fine-tuning
        weight_decay=0.01,
        use_cpu=True, # Force CPU because MPS fallback is causing 40-hour hangs
        load_best_model_at_end=True,
        metric_for_best_model="eval_f1",
        report_to="none" # Disable mlflow for this quick script
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["test"],
        compute_metrics=compute_metrics,
    )
    
    print("Starting Domain Adaptation Fine-Tuning...")
    trainer.train()
    
    print("Saving hardened model weights...")
    torch.save(trainer.model.state_dict(), bert_pth_path)
    print("Successfully overwrote model weights. Ready for inference!")

if __name__ == "__main__":
    main()
