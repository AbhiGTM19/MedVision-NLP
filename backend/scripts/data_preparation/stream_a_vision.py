import json
import os
import cv2
import easyocr
import numpy as np
from pathlib import Path
from tqdm import tqdm

import sys
# Ensure backend root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.data_preparation.preprocess_ocr import deskew

def preprocess_for_ocr(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    deskewed = deskew(thresh)
    final_img = cv2.bitwise_not(deskewed)
    return final_img

def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    processed_dir = base_dir / "dataset" / "processed"
    unified_path = processed_dir / "unified_dataset.jsonl"
    output_path = processed_dir / "unified_dataset_with_ocr.jsonl"
    
    if not unified_path.exists():
        print("Unified dataset not found.")
        return
        
    print("Initializing EasyOCR (optimizing for M1 if possible)...")
    try:
        # EasyOCR uses PyTorch. gpu=True will use MPS if PyTorch is built with it.
        reader = easyocr.Reader(['en'], gpu=True)
    except Exception:
        print("Falling back to CPU mode for EasyOCR.")
        reader = easyocr.Reader(['en'], gpu=False)

    records = []
    with open(unified_path, 'r') as f:
        for line in f:
            records.append(json.loads(line))
            
    images_to_process = [r for r in records if r.get('modality') == 'image']
    print(f"Found {len(images_to_process)} image records. Beginning Stream A Vision pipeline...")
    
    for record in tqdm(records, desc="Extracting OCR Features"):
        if record.get('modality') == 'image':
            img_path = base_dir / "dataset" / record['file_path']
            if not img_path.exists():
                print(f"Missing image: {img_path}")
                record['ocr_features'] = []
                continue
                
            preprocessed = preprocess_for_ocr(str(img_path))
            if preprocessed is None:
                record['ocr_features'] = []
                continue
                
            # Run EasyOCR
            results = reader.readtext(preprocessed)
            
            # Extract Text, Bounding Boxes, and Confidence Scores
            # Results format: [([[x1,y1], [x2,y1], [x2,y2], [x1,y2]], 'text', confidence_score), ...]
            ocr_features = []
            for bbox, text, conf in results:
                ocr_features.append({
                    "bbox": [[int(coord[0]), int(coord[1])] for coord in bbox],
                    "text": text,
                    "confidence": float(conf)
                })
            
            record['ocr_features'] = ocr_features
            # We append the average confidence score to the record for model weighting
            avg_conf = sum([f['confidence'] for f in ocr_features]) / len(ocr_features) if ocr_features else 0.0
            record['avg_ocr_confidence'] = avg_conf

    # Save the updated dataset
    print(f"Saving enriched dataset to {output_path}...")
    with open(output_path, 'w') as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
            
    print("Stream A Execution Complete. Vision features extracted!")

if __name__ == "__main__":
    main()
