import os
import json
import pandas as pd
from pathlib import Path
from tqdm import tqdm

def process_mtsamples(raw_dir):
    mtsamples_path = raw_dir / "mtsamples.csv"
    unified_records = []
    if not mtsamples_path.exists():
        print("mtsamples.csv not found.")
        return unified_records
        
    df = pd.read_csv(mtsamples_path)
    df = df.dropna(subset=['transcription'])
    
    for idx, row in df.iterrows():
        record = {
            "id": f"mtsamples_{idx}",
            "source": "mtsamples",
            "modality": "text",
            "file_path": None,
            "text": str(row['transcription']),
            "label": str(row.get('medical_specialty', 'Unknown')).strip()
        }
        unified_records.append(record)
        
    print(f"Processed {len(unified_records)} NLP records from mtsamples.")
    return unified_records

def process_synthetic_prescriptions(raw_dir):
    synthetic_dir = raw_dir / "medical-prescription-dataset"
    unified_records = []
    if not synthetic_dir.exists():
        print("medical-prescription-dataset not found.")
        return unified_records
        
    # Check train, val, test splits
    for split in ["train", "val", "test"]:
        split_dir = synthetic_dir / split
        if not split_dir.exists():
            continue
            
        annotations_dir = split_dir / "annotations"
        images_dir = split_dir / "images"
        
        if not annotations_dir.exists():
            continue
            
        for ann_file in annotations_dir.glob("*.json"):
            with open(ann_file, 'r') as f:
                try:
                    data = json.load(f)
                except:
                    continue
            
            ground_truth = data.get('ground_truth', '')
            base_name = ann_file.stem
            
            # Find matching image
            img_path = images_dir / f"{base_name}.png"
            if not img_path.exists():
                img_path = images_dir / f"{base_name}.jpg"
                
            record = {
                "id": f"prescription_{split}_{base_name}",
                "source": "medical-prescription-dataset",
                "modality": "image",
                "file_path": str(img_path.relative_to(raw_dir.parent)) if img_path.exists() else None,
                "text": ground_truth,
                "label": "Prescription"
            }
            unified_records.append(record)
            
    print(f"Processed {len(unified_records)} Image records from synthetic prescriptions.")
    return unified_records

def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    raw_dir = base_dir / "dataset" / "raw"
    processed_dir = base_dir / "dataset" / "processed"
    os.makedirs(processed_dir, exist_ok=True)
    
    all_records = []
    all_records.extend(process_mtsamples(raw_dir))
    all_records.extend(process_synthetic_prescriptions(raw_dir))
    
    out_path = processed_dir / "unified_dataset.jsonl"
    with open(out_path, 'w') as f:
        for r in all_records:
            f.write(json.dumps(r) + "\n")
            
    print(f"Successfully generated unified dataset with {len(all_records)} records at {out_path}.")

if __name__ == "__main__":
    main()
