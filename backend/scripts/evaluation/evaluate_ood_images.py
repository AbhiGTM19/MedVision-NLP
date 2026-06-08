import os
import sys
import torch
import easyocr
import cv2
import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from tqdm import tqdm
from collections import defaultdict
from transformers import AutoTokenizer

# Ensure backend directory is in sys.path
base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from core.architectures.dual_stream_ner import DualStreamFusionNER
from scripts.data_preparation.preprocess_ocr import deskew

def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")

def preprocess_image(img_path):
    img = cv2.imread(str(img_path))
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    deskewed = deskew(thresh)
    return cv2.bitwise_not(deskewed)

def evaluate_ood():
    print("🔬 MedVision-NLP: Real-World OOD Evaluation Pipeline")
    print("-" * 50)
    
    device = get_device()
    print(f"🖥️  Using Compute Device: {device}")
    
    data_dir = base_dir / 'dataset' / 'test_samples' / 'data'
    images = list(data_dir.glob('*.jpg')) + list(data_dir.glob('*.png'))
    if not images:
        print("❌ No images found in test_samples/data!")
        return
        
    print(f"✅ Found {len(images)} Out-Of-Distribution Test Images.")
    
    # 1. Initialize Everything
    tokenizer = AutoTokenizer.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")
    unique_tags = ['O', 'B-PATIENT_AGE', 'B-SIGNATURE', 'I-PATIENT_NAME', 'I-CLINIC_NAME', 
                   'B-CLINIC_NAME', 'B-DATE', 'I-MEDICATIONS', 'B-PATIENT_NAME', 
                   'B-CLINIC_ADDRESS', 'B-MEDICATIONS', 'I-CLINIC_ADDRESS', 'I-SIGNATURE']
    id2tag = {i: tag for i, tag in enumerate(unique_tags)}
    num_classes = len(unique_tags)
    
    model = DualStreamFusionNER(bert_hidden_size=768, num_classes=num_classes)
    weights_path = base_dir / 'models' / 'saved_weights' / 'dual_stream_ner_best.pth'
    
    checkpoint = torch.load(weights_path, map_location=device)
    state_dict = checkpoint.get('model_state_dict', checkpoint)
    new_state_dict = {k[7:] if k.startswith('module.') else k: v for k, v in state_dict.items()}
    model.load_state_dict(new_state_dict)
    model.to(device)
    model.eval()
    
    reader = easyocr.Reader(['en'], gpu=(device.type != 'cpu'))
    
    # Track Metrics
    entity_counts = defaultdict(int)
    entity_confidences = defaultdict(list)
    failed_ocr = 0
    
    print("\n🚀 Commencing Inference Sweep across 129 images...")
    
    for img_path in tqdm(images, desc="Processing Images"):
        preprocessed = preprocess_image(img_path)
        if preprocessed is None:
            failed_ocr += 1
            continue
            
        results = reader.readtext(preprocessed)
        if not results:
            failed_ocr += 1
            continue
            
        ocr_features = []
        for bbox, text, conf in results:
            ocr_features.append({
                "bbox": [[int(coord[0]), int(coord[1])] for coord in bbox],
                "confidence": float(conf)
            })
            
        full_text = " ".join([res[1] for res in results])
        tokens = full_text.split()
        if not tokens:
            continue
            
        avg_conf = sum([f['confidence'] for f in ocr_features]) / len(ocr_features)
        x1 = sum([f['bbox'][0][0] for f in ocr_features]) / len(ocr_features)
        y1 = sum([f['bbox'][0][1] for f in ocr_features]) / len(ocr_features)
        x2 = sum([f['bbox'][2][0] for f in ocr_features]) / len(ocr_features)
        y2 = sum([f['bbox'][2][1] for f in ocr_features]) / len(ocr_features)
        vision_meta = [avg_conf, x1, y1, x2, y2]
        
        encoding = tokenizer(
            tokens, is_split_into_words=True, return_offsets_mapping=False,
            padding='max_length', truncation=True, max_length=512
        )
        
        input_ids = torch.tensor([encoding['input_ids']], dtype=torch.long).to(device)
        attention_mask = torch.tensor([encoding['attention_mask']], dtype=torch.long).to(device)
        v_meta = torch.tensor([vision_meta], dtype=torch.float32).to(device)
        
        with torch.no_grad():
            logits = model(input_ids, attention_mask, v_meta)
            # Apply softmax to get confidence score of prediction
            probs = torch.softmax(logits, dim=2)
            max_probs, predictions = torch.max(probs, dim=2)
            
            predictions = predictions[0].cpu().numpy()
            max_probs = max_probs[0].cpu().numpy()
            
        word_ids = encoding.word_ids()
        previous_word_idx = None
        
        for i, word_idx in enumerate(word_ids):
            if word_idx is None or word_idx == previous_word_idx:
                continue
                
            tag_id = predictions[i]
            tag = id2tag[tag_id]
            conf = float(max_probs[i])
            
            if tag != 'O':
                entity_counts[tag] += 1
                entity_confidences[tag].append(conf)
                
            previous_word_idx = word_idx

    # Plot and Save Metrics
    static_dir = base_dir.parent / 'frontend' / 'static'
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # Compute Average Confidences
    avg_confidences = {tag: (sum(confs)/len(confs)) for tag, confs in entity_confidences.items()}
    
    # Save JSON
    ood_results = {
        "total_images": len(images),
        "failed_ocr": failed_ocr,
        "entity_counts": entity_counts,
        "average_confidences": avg_confidences
    }
    with open(static_dir / 'ood_evaluation_results.json', 'w') as f:
        json.dump(ood_results, f, indent=4)
        
    # Plot 1: Entity Counts
    tags = list(entity_counts.keys())
    counts = list(entity_counts.values())
    
    plt.figure(figsize=(12, 6))
    sns.barplot(x=counts, y=tags, palette='mako')
    plt.title('Total Entities Yield from OOD Prescriptions', fontsize=16, fontweight='bold')
    plt.xlabel('Total Instances Extracted', fontsize=12)
    plt.ylabel('Entity Type', fontsize=12)
    for i, v in enumerate(counts):
        plt.text(v + 0.1, i, str(v), color='black', va='center')
    plt.tight_layout()
    plt.savefig(static_dir / 'ood_entity_counts.png', dpi=300)
    plt.close()
    
    # Plot 2: Average Confidence
    tags_conf = list(avg_confidences.keys())
    confs = list(avg_confidences.values())
    
    plt.figure(figsize=(12, 6))
    sns.barplot(x=confs, y=tags_conf, palette='rocket')
    plt.title('Average Extraction Confidence per Entity Type (OOD Data)', fontsize=16, fontweight='bold')
    plt.xlabel('Neural Network Confidence (Softmax Probability)', fontsize=12)
    plt.ylabel('Entity Type', fontsize=12)
    plt.xlim(0, 1.0)
    for i, v in enumerate(confs):
        plt.text(v + 0.01, i, f"{v:.2f}", color='black', va='center')
    plt.tight_layout()
    plt.savefig(static_dir / 'ood_confidence_scores.png', dpi=300)
    plt.close()

    print("\n✅ OOD Evaluation Complete!")
    print(f"📝 Analyzed {len(images)} raw images.")
    print(f"📁 Generated Assets: ood_entity_counts.png, ood_confidence_scores.png")

if __name__ == "__main__":
    evaluate_ood()
