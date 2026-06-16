import glob
import io
import os

import pandas as pd
import pytesseract
import torch
import torch.nn.functional as F
from PIL import Image
from tqdm import tqdm
from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer

print("=== MedVision End-to-End Pipeline Evaluation ===")

# --- Configuration ---
BASE_DIR = "/Users/abhi/Downloads/AI ML/MedVision-NLP"
MODELS_DIR = os.path.join(BASE_DIR, "backend/models")
BERT_DIR = os.path.join(MODELS_DIR, "bio_clinicalBERT")

# Datasets
TEST_SAMPLES_DIR = os.path.join(BASE_DIR, "backend/dataset/test_samples/Handwritten_Medical_Prescriptions_Collection")
PARQUET_DIR = os.path.join(BASE_DIR, "backend/dataset/raw/medical_records_parsing_validation_set")

OUTPUT_CSV = os.path.join(BASE_DIR, "backend/scripts/evaluation/evaluation_results.csv")

# Device
device = torch.device("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}\n")

# --- 1. Load Bio_ClinicalBERT ---
print("Loading Bio_ClinicalBERT...")
bert_config = AutoConfig.from_pretrained(BERT_DIR)
tokenizer = AutoTokenizer.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")
bert_model = AutoModelForSequenceClassification.from_config(bert_config)

bert_pth_path = os.path.join(BERT_DIR, "bio_clinicalBERT_model.pth")
bert_model.load_state_dict(torch.load(bert_pth_path, map_location=device, weights_only=True))
bert_model.to(device)
bert_model.eval()

bert_model.eval()

# --- Utility Functions ---
def predict_pipeline(image: Image.Image) -> tuple[str, str, float]:
    """Runs Tesseract to get text, then BERT to get specialty classification."""
    image = image.convert("RGB")
    
    with torch.no_grad():
        # 1. Tesseract Generation
        extracted_text = pytesseract.image_to_string(image).strip()
        
        # 2. BERT Classification
        # If Tesseract failed to extract anything, we pass an empty string
        if not extracted_text.strip():
            return "", "Unknown", 0.0
            
        inputs = tokenizer(extracted_text, return_tensors="pt", padding="max_length", max_length=512, truncation=True).to(device)
        outputs = bert_model(**inputs)
        
        # Compute probabilities
        probs = F.softmax(outputs.logits, dim=-1)
        confidence, predicted_class_id = torch.max(probs, dim=-1)
        
        confidence = confidence.item()
        predicted_label = bert_config.id2label[predicted_class_id.item()]
        
    return extracted_text, predicted_label, confidence

# --- Evaluation Loop ---
results = []

# Process Image Folder
test_images = [
    "2.jpg",
    "10.jpg"
]

print(f"\nProcessing {len(test_images)} images from test_samples...")
for img_name in test_images:
    img_path = os.path.join(TEST_SAMPLES_DIR, img_name)
    if not os.path.exists(img_path):
        print(f"File not found: {img_path}")
        continue
    try:
        image = Image.open(img_path)
        text, specialty, conf = predict_pipeline(image)
        results.append({
            "source": f"test_samples/{img_name}",
            "extracted_text": text,
            "predicted_specialty": specialty,
            "confidence": conf
        })
    except Exception as e:
        print(f"Failed to process {img_name}: {e}")

# Process Parquet Files
parquet_files = glob.glob(os.path.join(PARQUET_DIR, "*.parquet"))
print("\nProcessing parquet files from medical_records_parsing_validation_set...")
parquet_processed = 0
for p_file in tqdm(parquet_files, desc="Processing Parquets"):
    if parquet_processed >= 5:
        break
    try:
        df = pd.read_parquet(p_file)
        if 'image' not in df.columns:
            continue
            
        for idx, row in df.iterrows():
            if parquet_processed >= 5:
                break
            source_name = f"{os.path.basename(p_file)}_row{idx}"
            try:
                # Load binary image
                image_bytes = row['image']
                if isinstance(image_bytes, dict) and 'bytes' in image_bytes:
                    image_bytes = image_bytes['bytes'] # Handle HF Dataset image format
                image = Image.open(io.BytesIO(image_bytes))
                
                text, specialty, conf = predict_pipeline(image)
                
                # Check what type of document the parquet file claims it is to compare against
                doc_type = row.get('document_type', 'Unknown')
                
                results.append({
                    "source": f"validation_set/{source_name} ({doc_type})",
                    "extracted_text": text,
                    "predicted_specialty": specialty,
                    "confidence": conf
                })
                parquet_processed += 1
            except Exception:
                # Ignore corrupted rows silently to continue evaluation
                pass
                
    except Exception as e:
        print(f"Failed to read parquet {p_file}: {e}")

# --- Save and Summarize ---
df_results = pd.DataFrame(results)
df_results.to_csv(OUTPUT_CSV, index=False)
print(f"\n✅ Evaluation complete. Saved {len(df_results)} records to {OUTPUT_CSV}")

print("\n--- TOP 5 HIGHEST CONFIDENCE PREDICTIONS ---")
print(df_results.sort_values("confidence", ascending=False).head(5)[["source", "predicted_specialty", "confidence"]].to_markdown(index=False))

print("\n--- TOP 5 LOWEST CONFIDENCE PREDICTIONS ---")
print(df_results.sort_values("confidence", ascending=True).head(5)[["source", "predicted_specialty", "confidence"]].to_markdown(index=False))

print("\nTo view all generated text and mappings, open the saved CSV file.")
