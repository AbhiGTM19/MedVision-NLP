import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
from tqdm import tqdm
import random
import numpy as np
import mlflow

import sys
# Ensure backend root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.architectures.dual_stream_ner import DualStreamFusionNER

def set_seed(seed=42):
    """Ensures 100% reproducibility across runs."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    elif torch.backends.mps.is_available():
        torch.mps.manual_seed(seed)

class FusedMedicalDataset(Dataset):
    def __init__(self, jsonl_path):
        self.records = []
        with open(jsonl_path, 'r') as f:
            for line in f:
                data = json.loads(line)
                if 'bert_embedding' in data:
                    self.records.append(data)
                    
        self.label_map = {"Surgery": 0, "Prescription": 1}
        
    def __len__(self):
        return len(self.records)
        
    def __getitem__(self, idx):
        record = self.records[idx]
        
        nlp_emb = torch.tensor(record['bert_embedding'], dtype=torch.float32)
        avg_conf = record.get('avg_ocr_confidence', 0.0)
        
        ocr_features = record.get('ocr_features', [])
        if ocr_features:
            x1 = sum([f['bbox'][0][0] for f in ocr_features]) / len(ocr_features)
            y1 = sum([f['bbox'][0][1] for f in ocr_features]) / len(ocr_features)
            x2 = sum([f['bbox'][2][0] for f in ocr_features]) / len(ocr_features)
            y2 = sum([f['bbox'][2][1] for f in ocr_features]) / len(ocr_features)
        else:
            x1, y1, x2, y2 = 0.0, 0.0, 0.0, 0.0
            
        vision_meta = torch.tensor([avg_conf, x1, y1, x2, y2], dtype=torch.float32)
        
        raw_label = record.get('label', 'Unknown')
        label_id = self.label_map.get(raw_label, 0)
        label_tensor = torch.tensor(label_id, dtype=torch.long)
        
        return nlp_emb, vision_meta, label_tensor

def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")

def train_model():
    set_seed(42)  # MLOps: Reproducibility
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_path = base_dir / "dataset" / "processed" / "unified_dataset_fused.jsonl"
    
    if not data_path.exists():
        print("Fusion dataset not found. Please wait for Stream B to complete.")
        return
        
    device = get_device()
    print(f"Training on {device}...")
    
    dataset = FusedMedicalDataset(data_path)
    
    # MLOps: Data pipeline optimization (num_workers and pin_memory)
    # Note: On macOS, num_workers > 0 can sometimes cause multiprocessing issues.
    # Set to 0 if issues occur, but 2 is a standard starting point.
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True, num_workers=2, pin_memory=True)
    
    model = DualStreamFusionNER(bert_hidden_size=768, num_classes=2).to(device)
    
    criterion = nn.CrossEntropyLoss()
    learning_rate = 1e-4
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    best_loss = float('inf')
    patience = 5
    patience_counter = 0
    epochs = 20
    
    # MLOps: Experiment Tracking via MLflow in a strict directory structure
    tracking_dir = base_dir / "models" / "tracking"
    os.makedirs(tracking_dir, exist_ok=True)
    mlflow.set_tracking_uri(f"sqlite:///{tracking_dir}/mlruns.db")
    mlflow.set_experiment("Dual_Stream_NER")
    
    with mlflow.start_run():
        # Log hyperparameters
        mlflow.log_params({
            "learning_rate": learning_rate,
            "batch_size": 32,
            "epochs": epochs,
            "optimizer": "Adam",
            "seed": 42
        })
        
        model.train()
        for epoch in range(epochs):
            total_loss = 0
            correct = 0
            total = 0
            
            progress = tqdm(dataloader, desc=f"Epoch {epoch+1}/{epochs}")
            for nlp_emb, vision_meta, labels in progress:
                # Move to device with non_blocking to pair with pin_memory=True
                nlp_emb = nlp_emb.to(device, non_blocking=True)
                vision_meta = vision_meta.to(device, non_blocking=True)
                labels = labels.to(device, non_blocking=True)
                
                # MLOps: More efficient gradient clearing
                optimizer.zero_grad(set_to_none=True)
                
                outputs = model(nlp_emb, vision_meta)
                loss = criterion(outputs, labels)
                
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
                
                progress.set_postfix({'loss': loss.item(), 'acc': correct/total})
                
            avg_loss = total_loss / len(dataloader)
            epoch_acc = correct / total
            
            # Log metrics per epoch
            mlflow.log_metric("train_loss", avg_loss, step=epoch)
            mlflow.log_metric("train_accuracy", epoch_acc, step=epoch)
            
            # MLOps: Advanced Checkpointing
            if avg_loss < best_loss:
                best_loss = avg_loss
                patience_counter = 0
                
                os.makedirs(base_dir / "models" / "saved_weights", exist_ok=True)
                checkpoint_path = base_dir / "models" / "saved_weights" / "dual_stream_fusion_best.pth"
                
                checkpoint = {
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'loss': best_loss,
                }
                torch.save(checkpoint, checkpoint_path)
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"Early stopping triggered at epoch {epoch+1}!")
                    break
                
        print("Training complete! Model successfully learned to fuse OCR metadata with BERT embeddings.")

if __name__ == "__main__":
    train_model()

