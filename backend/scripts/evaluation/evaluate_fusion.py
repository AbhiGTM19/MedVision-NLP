import os
import sys
import torch
import random
import numpy as np
from pathlib import Path
from tqdm import tqdm
from torch.utils.data import DataLoader, random_split
from transformers import AutoTokenizer
from sklearn.metrics import classification_report
import json
import matplotlib.pyplot as plt
import seaborn as sns

# Add backend directory to sys.path
base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from core.architectures.dual_stream_ner import DualStreamFusionNER
from core.dataset import FusedMedicalDataset

def set_seed(seed=42):
    """Enforce exact same seed as Kaggle training to perfectly reconstruct the holdout set"""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")

def evaluate():
    print("🔬 MedVision-NLP: Phase 2 Evaluation Pipeline")
    print("-" * 50)
    
    set_seed(42)
    device = get_device()
    print(f"🖥️  Using Compute Device: {device}")
    
    # 1. Paths
    dataset_path = base_dir / 'dataset' / 'processed' / 'unified_dataset_iob.jsonl'
    weights_path = base_dir / 'models' / 'saved_weights' / 'dual_stream_ner_best.pth'
    
    if not weights_path.exists():
        print(f"❌ Error: Model weights not found at {weights_path}")
        return
        
    # 2. Reconstruct Dataset & Validation Split
    print("📚 Reconstructing exactly matching Validation Holdout Set...")
    tokenizer = AutoTokenizer.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")
    
    # Temporarily suppress MPS warning for DataLoader pin_memory
    import warnings
    warnings.filterwarnings("ignore", message=".*pin_memory.*")
    
    full_dataset = FusedMedicalDataset(dataset_path, tokenizer, max_length=512)
    
    val_size = int(0.1 * len(full_dataset))
    train_size = len(full_dataset) - val_size
    _, val_dataset = random_split(full_dataset, [train_size, val_size])
    
    print(f"✅ Total Records: {len(full_dataset)} | Validation Holdout Size: {val_size}")
    
    val_dataloader = DataLoader(val_dataset, batch_size=8, shuffle=False, num_workers=0)
    
    # 3. Load Architecture & Inject Weights
    print("🧠 Initializing DualStreamFusionNER and loading Kaggle Weights...")
    num_classes = len(full_dataset.unique_tags)
    model = DualStreamFusionNER(bert_hidden_size=768, num_classes=num_classes)
    
    checkpoint = torch.load(weights_path, map_location=device)
    state_dict = checkpoint.get('model_state_dict', checkpoint)
    
    # Handle Kaggle's nn.DataParallel "module." prefix safely
    new_state_dict = {}
    for k, v in state_dict.items():
        if k.startswith('module.'):
            new_state_dict[k[7:]] = v
        else:
            new_state_dict[k] = v
            
    model.load_state_dict(new_state_dict)
    model.to(device)
    model.eval()
    print("✅ Weights loaded successfully.")
    
    # 4. Evaluation Loop
    all_preds = []
    all_labels = []
    
    print("🚀 Beginning Inference on Holdout Set...")
    with torch.no_grad():
        progress = tqdm(val_dataloader, desc="Evaluating")
        for input_ids, attention_mask, vision_meta, labels in progress:
            input_ids = input_ids.to(device)
            attention_mask = attention_mask.to(device)
            vision_meta = vision_meta.to(device)
            labels = labels.to(device)
            
            logits = model(input_ids, attention_mask, vision_meta)
            
            # Shape: (batch_size, seq_len, num_classes)
            logits_flat = logits.view(-1, num_classes)
            labels_flat = labels.view(-1)
            
            predictions = torch.argmax(logits_flat, dim=1)
            
            # Create a mask to strictly ignore all -100 subword/padding tokens
            mask = labels_flat != -100
            
            all_preds.extend(predictions[mask].cpu().numpy())
            all_labels.extend(labels_flat[mask].cpu().numpy())
            
    # 5. Calculate Metrics
    print("-" * 50)
    print("📊 Generating Mathematical Evaluation Report")
    
    # Reconstruct inverse tag mapping correctly to drop 'O'
    id2tag = {v: k for k, v in full_dataset.tag2id.items()}
    
    # We want to show metrics for everything. We will also show 'O' to be transparent,
    # but the terminal report will give us all details.
    target_names = [id2tag[i] for i in range(num_classes)]
    
    report = classification_report(
        all_labels, 
        all_preds, 
        target_names=target_names, 
        zero_division=0,
        digits=4
    )
    print(report)
    
    # Generate JSON and Graphs for the Frontend
    print("\n💾 Saving metrics and graphs for Frontend UI...")
    report_dict = classification_report(
        all_labels, 
        all_preds, 
        target_names=target_names, 
        zero_division=0,
        output_dict=True
    )
    
    static_dir = base_dir.parent / 'frontend' / 'static'
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Save JSON
    with open(static_dir / 'evaluation_metrics.json', 'w') as f:
        json.dump(report_dict, f, indent=4)
        
    # 2. Extract Data for Plotting (Ignore 'O' tag and summary averages)
    entities = []
    f1_scores = []
    precisions = []
    recalls = []
    
    for key, value in report_dict.items():
        if key not in ['O', 'accuracy', 'macro avg', 'weighted avg']:
            entities.append(key)
            f1_scores.append(value['f1-score'])
            precisions.append(value['precision'])
            recalls.append(value['recall'])
            
    # 3. Plot F1 Scores
    plt.figure(figsize=(12, 6))
    sns.barplot(x=f1_scores, y=entities, palette='viridis')
    plt.title('F1-Score per Medical Entity', fontsize=16, fontweight='bold')
    plt.xlabel('F1-Score', fontsize=12)
    plt.ylabel('Entity', fontsize=12)
    plt.xlim(0, 1.1)
    for i, v in enumerate(f1_scores):
        plt.text(v + 0.01, i, f"{v:.4f}", color='black', va='center')
    plt.tight_layout()
    plt.savefig(static_dir / 'f1_scores.png', dpi=300)
    plt.close()
    
    # 4. Plot Precision vs Recall
    fig, ax = plt.subplots(figsize=(12, 6))
    y_pos = np.arange(len(entities))
    height = 0.35
    
    ax.barh(y_pos - height/2, precisions, height, label='Precision', color='#3498db')
    ax.barh(y_pos + height/2, recalls, height, label='Recall', color='#e74c3c')
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(entities)
    ax.legend()
    ax.set_title('Precision vs Recall per Medical Entity', fontsize=16, fontweight='bold')
    ax.set_xlabel('Score')
    ax.set_xlim(0, 1.1)
    plt.tight_layout()
    plt.savefig(static_dir / 'precision_recall.png', dpi=300)
    plt.close()
    
    print(f"✅ Saved evaluation_metrics.json")
    print(f"✅ Saved f1_scores.png")
    print(f"✅ Saved precision_recall.png")
    print(f"📁 Assets located in: {static_dir}")

if __name__ == "__main__":
    evaluate()
