import os
import json
import re
import logging
import argparse
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path
from tqdm import tqdm
from transformers import AutoTokenizer
from image_preprocessing import normalize_image

# Configure Production Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('BuildUnifiedDataset')

def normalize_text(text: Any) -> str:
    """Robust NLP text cleaning for clinical notes."""
    if pd.isnull(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'</?s_ocr>', '', text)
    text = re.sub(r'</?s>', '', text)
    text = re.sub(r'[\:,;]\s*,', ',', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.encode("ascii", errors="ignore").decode()
    return text.strip()

def process_mtsamples(raw_dir: Path, tokenizer: AutoTokenizer) -> List[Dict[str, Any]]:
    """Processes MTSamples CSV into exactly chunked Bio_ClinicalBERT text records."""
    mtsamples_path = raw_dir / "mtsamples.csv"
    unified_records = []
    
    if not mtsamples_path.exists():
        logger.warning(f"File not found: {mtsamples_path}")
        return unified_records
        
    try:
        df = pd.read_csv(mtsamples_path).dropna(subset=['transcription'])
        df = df.drop_duplicates(subset=['transcription'])
        
        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing MTSamples"):
            text = normalize_text(row['transcription'])
            
            # Mathematically perfect chunking at exactly 510 subword tokens (leaving 2 for CLS/SEP)
            tokens = tokenizer.encode(text, add_special_tokens=False)
            chunk_size = 510
            
            raw_label = str(row.get('medical_specialty', 'Unknown')).strip()
            label = raw_label if raw_label else "Unknown"
            
            for i in range(0, len(tokens), chunk_size):
                chunk_tokens = tokens[i:i + chunk_size]
                chunk_text = tokenizer.decode(chunk_tokens)
                
                unified_records.append({
                    "id": f"mtsamples_{idx}_chunk_{i//chunk_size}",
                    "source": "mtsamples",
                    "modality": "text",
                    "text": chunk_text,
                    "label": label
                })
        logger.info(f"Generated {len(unified_records)} perfectly sized token chunks from MTSamples.")
    except Exception as e:
        logger.error(f"Failed to process MTSamples: {str(e)}")
        
    return unified_records

def process_mimic_iv(raw_dir: Path) -> List[Dict[str, Any]]:
    """Processes MIMIC-IV prescriptions and diagnoses into semantic clinical sentences."""
    mimic_dir = raw_dir / "mimic-iv-clinical-database-demo-2.2" / "hosp"
    unified_records = []
    
    presc_path = mimic_dir / "prescriptions.csv"
    diag_path = mimic_dir / "diagnoses_icd.csv"
    
    if not presc_path.exists() or not diag_path.exists():
        logger.warning("MIMIC-IV files not found.")
        return unified_records
        
    try:
        # Prevent memory explosion by bounding row counts before inner merge
        df_presc = pd.read_csv(presc_path).dropna(subset=['subject_id', 'hadm_id', 'drug']).head(10000)
        df_diag = pd.read_csv(diag_path).dropna(subset=['subject_id', 'hadm_id', 'icd_code']).head(10000)
        
        merged = pd.merge(df_presc, df_diag, on=['subject_id', 'hadm_id'], how='inner')
        merged = merged.drop_duplicates(subset=['drug', 'icd_code']).head(5000)
        
        for idx, row in tqdm(merged.iterrows(), total=len(merged), desc="Processing MIMIC-IV"):
            route = str(row['route']) if pd.notnull(row['route']) else "an unspecified"
            raw_text = f"Patient diagnosed with ICD code {row['icd_code']} was prescribed {row['drug']} via {route} route."
            
            unified_records.append({
                "id": f"mimic_{row['subject_id']}_{row['hadm_id']}_{idx}",
                "source": "mimic-iv",
                "modality": "text",
                "text": normalize_text(raw_text),
                "label": "Prescription/Diagnosis"
            })
        logger.info(f"Generated {len(unified_records)} text records from MIMIC-IV.")
    except Exception as e:
        logger.error(f"Failed to process MIMIC-IV: {str(e)}")
        
    return unified_records

def process_synthetic_prescriptions(raw_dir: Path, processed_img_dir: Path) -> List[Dict[str, Any]]:
    """Processes synthetic prescription images and ground truth text."""
    synthetic_dir = raw_dir / "medical-prescription-dataset"
    unified_records = []
    
    if not synthetic_dir.exists():
        logger.warning(f"Directory not found: {synthetic_dir}")
        return unified_records
        
    for split in ["train", "val", "test"]:
        split_dir = synthetic_dir / split
        if not split_dir.exists():
            continue
            
        annotations_dir = split_dir / "annotations"
        images_dir = split_dir / "images"
        if not annotations_dir.exists():
            continue
            
        json_files = list(annotations_dir.glob("*.json"))
        for ann_file in tqdm(json_files, desc=f"Processing Synthetic {split.capitalize()}"):
            try:
                with open(ann_file, 'r') as f:
                    data = json.load(f)
                ground_truth = data.get('ground_truth', '')
                base_name = ann_file.stem
                
                img_path = images_dir / f"{base_name}.png"
                if not img_path.exists():
                    img_path = images_dir / f"{base_name}.jpg"
                    
                if img_path.exists():
                    final_img_path = normalize_image(str(img_path), str(processed_img_dir))
                    if final_img_path:
                        rel_path = str(Path(final_img_path).relative_to(raw_dir.parent.parent))
                        unified_records.append({
                            "id": f"prescription_{split}_{base_name}",
                            "source": "medical-prescription-dataset",
                            "modality": "image",
                            "file_path": rel_path,
                            "text": normalize_text(ground_truth)
                        })
            except Exception as e:
                logger.error(f"Error processing {ann_file.name}: {str(e)}")
                
    logger.info(f"Generated {len(unified_records)} image records from Synthetic Prescriptions.")
    return unified_records

def process_raw_handwritten(raw_dir: Path, processed_img_dir: Path) -> List[Dict[str, Any]]:
    """Processes raw handwritten word images using dynamic filename-based label extraction."""
    hw_words = raw_dir / "Medical_Prescription_Handwritten_Words"
    unified_records = []
    
    if not hw_words.exists():
        logger.warning(f"Directory not found: {hw_words}")
        return unified_records
        
    images = list(hw_words.rglob("*.jpg")) + list(hw_words.rglob("*.png"))
    data_csv = hw_words / "data.csv"
    label_map = {}
    
    if data_csv.exists():
        try:
            df = pd.read_csv(data_csv)
            if len(df.columns) >= 2:
                label_map = dict(zip(df.iloc[:,0], df.iloc[:,1]))
        except Exception as e:
            logger.warning(f"Failed to parse label CSV: {str(e)}")
            
    for img in tqdm(images, desc="Processing Handwritten Words"):
        try:
            text = label_map.get(img.name, "")
            if not text:
                text = img.stem # Fallback: use the filename itself as the ground truth label
                
            final_img_path = normalize_image(str(img), str(processed_img_dir))
            if final_img_path:
                rel_path = str(Path(final_img_path).relative_to(raw_dir.parent.parent))
                unified_records.append({
                    "id": f"hw_words_{img.stem}",
                    "source": "handwritten_words",
                    "modality": "image",
                    "file_path": rel_path,
                    "text": normalize_text(text)
                })
        except Exception as e:
            logger.error(f"Error processing {img.name}: {str(e)}")
            
    logger.info(f"Generated {len(unified_records)} image records from Handwritten Words.")
    return unified_records

def main():
    parser = argparse.ArgumentParser(description="MedVision Unified Dataset Builder")
    parser.add_argument("--base_dir", type=str, default=str(Path(__file__).resolve().parent.parent.parent), help="Root backend directory")
    args = parser.parse_args()
    
    base_dir = Path(args.base_dir)
    raw_dir = base_dir / "dataset" / "raw"
    processed_dir = base_dir / "dataset" / "processed"
    processed_img_dir = processed_dir / "images"
    
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(processed_img_dir, exist_ok=True)
    
    logger.info("Initializing Native Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")
    
    logger.info("Initializing Dataset Build Pipeline...")
    
    # Text Modality (Bio_ClinicalBERT)
    text_records = []
    text_records.extend(process_mtsamples(raw_dir, tokenizer))
    text_records.extend(process_mimic_iv(raw_dir))
    
    bio_bert_path = processed_dir / "bio_clinicalbert_dataset.jsonl"
    with open(bio_bert_path, 'w') as f:
        for r in text_records:
            f.write(json.dumps(r) + "\n")
    logger.info(f"Successfully saved {len(text_records)} Bio_ClinicalBERT records to {bio_bert_path.name}")
            
    # Vision Modality (TrOCR)
    image_records = []
    image_records.extend(process_synthetic_prescriptions(raw_dir, processed_img_dir))
    image_records.extend(process_raw_handwritten(raw_dir, processed_img_dir))
    
    trocr_path = processed_dir / "trocr_dataset.jsonl"
    with open(trocr_path, 'w') as f:
        for r in image_records:
            if r["text"]: # Strict filter to ensure no empty labels exist
                f.write(json.dumps(r) + "\n")
    logger.info(f"Successfully saved TrOCR records to {trocr_path.name}")
    logger.info("Pipeline Complete.")

if __name__ == "__main__":
    main()
