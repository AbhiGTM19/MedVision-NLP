import json
import torch
from pathlib import Path
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModel

import sys
# Ensure backend root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.data_preparation.preprocess_nlp import clean_text

def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")

def get_embedding(text, model, tokenizer, device):
    """Generates a 768-dimensional Bio_ClinicalBERT embedding for the text."""
    # Truncate text if it's too long for BERT (max 512 tokens)
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding="max_length")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model(**inputs)
        
    # Pool the output (take the mean of the last hidden state)
    embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
    return embeddings.tolist()

def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    processed_dir = base_dir / "dataset" / "processed"
    
    # Wait for Stream A to finish, so we chain off its output
    input_path = processed_dir / "unified_dataset_with_ocr.jsonl"
    output_path = processed_dir / "unified_dataset_fused.jsonl"
    
    if not input_path.exists():
        print(f"File not found: {input_path}")
        print("Please ensure Stream A (Vision) finishes before running Stream B.")
        return

    device = get_device()
    print(f"Initializing Bio_ClinicalBERT on {device}...")
    
    model_name = "emilyalsentzer/Bio_ClinicalBERT"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name).to(device)
    model.eval()

    records = []
    with open(input_path, 'r') as f:
        for line in f:
            records.append(json.loads(line))
            
    print(f"Loaded {len(records)} records. Extracting dense semantic embeddings...")
    
    for record in tqdm(records, desc="Stream B NLP Pipeline"):
        text_to_embed = ""
        
        # If it's text modality from MTSamples/MIMIC
        if record.get('modality') == 'text':
            raw_text = record.get('text', '')
            text_to_embed = clean_text(raw_text)
            
        # If it's an image from Prescription dataset, embed the OCR output!
        elif record.get('modality') == 'image':
            ocr_features = record.get('ocr_features', [])
            raw_text = " ".join([feat['text'] for feat in ocr_features])
            text_to_embed = clean_text(raw_text)
            
        if not text_to_embed.strip():
            record['bert_embedding'] = [0.0] * 768
            continue
            
        embedding = get_embedding(text_to_embed, model, tokenizer, device)
        record['bert_embedding'] = embedding

    print(f"Saving final fused dataset to {output_path}...")
    with open(output_path, 'w') as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
            
    print("Stream B Execution Complete. NLP features extracted and fused!")

if __name__ == "__main__":
    main()
