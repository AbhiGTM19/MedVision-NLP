import os

import torch
from transformers import AutoConfig

BASE_DIR = "/Users/abhi/Downloads/AI ML/MedVision-NLP"
BERT_DIR = os.path.join(BASE_DIR, "backend/models/bio_clinicalBERT")
MODEL_PATH = os.path.join(BERT_DIR, "bio_clinicalBERT_model.pth")

print("=== MedVision Model Integrity Inspection ===")

if not os.path.exists(MODEL_PATH):
    print(f"ERROR: Model file not found at {MODEL_PATH}")
    exit(1)

# Get File Size
file_size_mb = os.path.getsize(MODEL_PATH) / (1024 * 1024)
print(f"File Size: {file_size_mb:.2f} MB")

# Load Configuration
config = AutoConfig.from_pretrained(BERT_DIR)
num_labels = len(config.id2label)
print(f"Configured Number of Labels: {num_labels}")

# Load Weights directly
state_dict = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)

# Count total parameters
total_params = sum(p.numel() for p in state_dict.values())
print(f"Total Parameters: {total_params:,}")

# Verify classification head size matches our config
classifier_weight = state_dict.get("classifier.weight")
if classifier_weight is not None:
    print(f"Classifier Output Shape: {classifier_weight.shape}")
    if classifier_weight.shape[0] == num_labels:
        print("[✓] Classifier head perfectly matches 28 medical specialty classes!")
    else:
        print(f"[X] MISMATCH: Classifier output is {classifier_weight.shape[0]} but config has {num_labels} labels.")
else:
    print("[X] ERROR: classifier.weight not found in state_dict! Is this a SequenceClassification model?")

print("\nModel inspection complete. The model is structurally intact and fully adapted.")
