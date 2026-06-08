import os
import sys
import torch
import easyocr
from pathlib import Path
from transformers import AutoTokenizer

# Ensure backend directory is in sys.path
base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from core.architectures.dual_stream_ner import DualStreamFusionNER
from scripts.data_preparation.preprocess_ocr import deskew
import cv2

def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")

class MedVisionInferenceEngine:
    def __init__(self):
        print("🧠 Booting Neural Inference Engine...")
        self.device = get_device()
        self.tokenizer = AutoTokenizer.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")
        
        # Tags array MUST perfectly match the dataset tag2id logic
        self.unique_tags = ['O', 'B-PATIENT_AGE', 'B-SIGNATURE', 'I-PATIENT_NAME', 'I-CLINIC_NAME', 
                            'B-CLINIC_NAME', 'B-DATE', 'I-MEDICATIONS', 'B-PATIENT_NAME', 
                            'B-CLINIC_ADDRESS', 'B-MEDICATIONS', 'I-CLINIC_ADDRESS', 'I-SIGNATURE']
        self.id2tag = {i: tag for i, tag in enumerate(self.unique_tags)}
        
        # Load Architecture & Weights
        self.model = DualStreamFusionNER(bert_hidden_size=768, num_classes=len(self.unique_tags))
        weights_path = base_dir / 'models' / 'saved_weights' / 'dual_stream_ner_best.pth'
        
        if not weights_path.exists():
            raise FileNotFoundError(f"Model weights missing: {weights_path}")
            
        checkpoint = torch.load(weights_path, map_location=self.device)
        state_dict = checkpoint.get('model_state_dict', checkpoint)
        
        # Strip DataParallel prefix if present
        new_state_dict = {k[7:] if k.startswith('module.') else k: v for k, v in state_dict.items()}
        self.model.load_state_dict(new_state_dict)
        self.model.to(self.device)
        self.model.eval()
        
        # Initialize EasyOCR
        print("👁️ Initializing Vision Stream (EasyOCR)...")
        self.reader = easyocr.Reader(['en'], gpu=(self.device.type != 'cpu'))
        print("✅ Systems Online.")

    def preprocess_image(self, img_path):
        """Identical preprocessing to the training pipeline for maximum accuracy."""
        img = cv2.imread(str(img_path))
        if img is None:
            raise ValueError(f"Could not load image: {img_path}")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        deskewed = deskew(thresh)
        return cv2.bitwise_not(deskewed)

    def extract_entities(self, text: str, vision_meta: list):
        """Core inference loop."""
        tokens = text.split()
        if not tokens:
            return []
            
        encoding = self.tokenizer(
            tokens,
            is_split_into_words=True,
            return_offsets_mapping=False,
            padding='max_length',
            truncation=True,
            max_length=512
        )
        
        input_ids = torch.tensor([encoding['input_ids']], dtype=torch.long).to(self.device)
        attention_mask = torch.tensor([encoding['attention_mask']], dtype=torch.long).to(self.device)
        v_meta = torch.tensor([vision_meta], dtype=torch.float32).to(self.device)
        
        with torch.no_grad():
            logits = self.model(input_ids, attention_mask, v_meta)
            predictions = torch.argmax(logits, dim=2)[0].cpu().numpy()
            
        word_ids = encoding.word_ids()
        
        extracted = []
        previous_word_idx = None
        for i, word_idx in enumerate(word_ids):
            if word_idx is None or word_idx == previous_word_idx:
                continue
                
            tag_id = predictions[i]
            tag = self.id2tag[tag_id]
            
            if tag != 'O':
                extracted.append((tokens[word_idx], tag))
                
            previous_word_idx = word_idx
            
        return extracted

    def test_text(self, text: str):
        print("\n" + "="*50)
        print(f"📝 TEXT INFERENCE: {text}")
        print("="*50)
        # Dummy vision metadata for raw text
        vision_meta = [0.0, 0.0, 0.0, 0.0, 0.0]
        entities = self.extract_entities(text, vision_meta)
        self._print_results(entities)

    def test_image(self, image_path: str):
        print("\n" + "="*50)
        print(f"🖼️ IMAGE INFERENCE: {image_path}")
        print("="*50)
        
        preprocessed = self.preprocess_image(image_path)
        results = self.reader.readtext(preprocessed)
        
        if not results:
            print("❌ OCR failed to extract any text.")
            return
            
        ocr_features = []
        for bbox, text, conf in results:
            ocr_features.append({
                "bbox": [[int(coord[0]), int(coord[1])] for coord in bbox],
                "confidence": float(conf)
            })
            
        full_text = " ".join([res[1] for res in results])
        print(f"Extracted Text: {full_text[:100]}...")
        
        avg_conf = sum([f['confidence'] for f in ocr_features]) / len(ocr_features)
        x1 = sum([f['bbox'][0][0] for f in ocr_features]) / len(ocr_features)
        y1 = sum([f['bbox'][0][1] for f in ocr_features]) / len(ocr_features)
        x2 = sum([f['bbox'][2][0] for f in ocr_features]) / len(ocr_features)
        y2 = sum([f['bbox'][2][1] for f in ocr_features]) / len(ocr_features)
        
        vision_meta = [avg_conf, x1, y1, x2, y2]
        
        entities = self.extract_entities(full_text, vision_meta)
        self._print_results(entities)
        
    def _print_results(self, entities):
        if not entities:
            print("❌ No medical entities detected.")
            return
            
        print("\n💉 DETECTED ENTITIES:")
        print("-" * 30)
        for word, tag in entities:
            print(f"{tag.ljust(20)} | {word}")

def main():
    engine = MedVisionInferenceEngine()
    
    while True:
        print("\nOptions:")
        print("1. Type custom text manually")
        print("2. Test an image path (e.g. out-of-distribution prescription)")
        print("3. Exit")
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == '1':
            text = input("\nEnter clinical text: ").strip()
            if text:
                engine.test_text(text)
        elif choice == '2':
            path = input("\nEnter absolute or relative image path: ").strip()
            if os.path.exists(path):
                engine.test_image(path)
            else:
                print("❌ File does not exist.")
        elif choice == '3':
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
