import os
import io
import glob
import random
import pandas as pd
from PIL import Image
import pytesseract
from tqdm import tqdm

BASE_DIR = "/Users/abhi/Downloads/AI ML/MedVision-NLP"
PARQUET_DIR = os.path.join(BASE_DIR, "backend/dataset/raw/medical_records_parsing_validation_set")
MTSAMPLES_CSV = os.path.join(BASE_DIR, "backend/dataset/raw/mtsamples.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "backend/dataset/processed/tesseract_finetune_data.csv")

os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

# 1. OCR Noise Injector for text dataset
def inject_ocr_noise(text):
    if not isinstance(text, str):
        return text
        
    replacements = {
        'o': '0', 'O': '0',
        'l': '1', 'I': 'l', '1': 'l',
        't': 'f', 'f': 't',
        'm': 'rn', 'rn': 'm',
        'c': 'e', 'e': 'c',
        '.': ',', ',': '.'
    }
    
    chars = list(text)
    # Inject noise in roughly 5% of characters to mimic poor OCR
    for i in range(len(chars)):
        if random.random() < 0.05 and chars[i] in replacements:
            chars[i] = replacements[chars[i]]
            
    # Randomly drop a character (1% chance)
    chars = [c for c in chars if random.random() > 0.01]
    
    return "".join(chars)

def generate_dataset():
    data = []
    
    # --- Part A: Tesseract on Parquet Images ---
    parquet_files = glob.glob(os.path.join(PARQUET_DIR, "*.parquet"))
    print(f"Found {len(parquet_files)} parquet files. Extracting with Tesseract...")
    
    # We map common document_types from the validation set to our valid labels if needed
    doc_type_mapping = {
        "Lab-report": "SOAP / Chart / Progress Notes", # Fallback for lab reports
        "Prescription": "Prescription/Diagnosis"
    }
    
    for p_file in tqdm(parquet_files, desc="Parquet OCR"):
        try:
            df = pd.read_parquet(p_file)
            if 'image' not in df.columns:
                continue
                
            for _, row in df.iterrows():
                try:
                    image_bytes = row['image']
                    if isinstance(image_bytes, dict) and 'bytes' in image_bytes:
                        image_bytes = image_bytes['bytes']
                        
                    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                    text = pytesseract.image_to_string(image).strip()
                    
                    if not text:
                        continue
                        
                    raw_type = row.get('document_type', 'Other')
                    label = doc_type_mapping.get(raw_type, raw_type)
                    
                    data.append({
                        "text": text,
                        "label": label,
                        "source": "tesseract_image"
                    })
                except Exception as e:
                    pass
        except Exception as e:
            print(f"Error reading {p_file}: {e}")
            
    # --- Part B: MTSamples with Noise ---
    print("\nLoading mtsamples.csv and injecting noise...")
    try:
        mt_df = pd.read_csv(MTSAMPLES_CSV)
        # Drop rows missing transcription
        mt_df = mt_df.dropna(subset=['transcription', 'medical_specialty'])
        
        # We only need a subset to balance with the image dataset, e.g. 1500 samples
        # Sample evenly across classes if possible, or just random
        mt_df_sampled = mt_df.sample(n=1500, random_state=42)
        
        for _, row in tqdm(mt_df_sampled.iterrows(), total=len(mt_df_sampled), desc="Injecting Noise"):
            label = str(row['medical_specialty']).strip()
            # Clean up some common labels that might have ' / ' vs '/' 
            # In mtsamples it's usually e.g. " Surgery", " SOAP / Chart / Progress Notes"
            
            noisy_text = inject_ocr_noise(row['transcription'])
            data.append({
                "text": noisy_text,
                "label": label,
                "source": "mtsamples_noisy"
            })
    except Exception as e:
        print(f"Error reading mtsamples.csv: {e}")
        
    # --- Save ---
    final_df = pd.DataFrame(data)
    
    # Basic label cleanup to match config.json exactly
    final_df['label'] = final_df['label'].str.strip()
    
    final_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nGenerated dataset with {len(final_df)} samples at: {OUTPUT_CSV}")

if __name__ == "__main__":
    generate_dataset()
