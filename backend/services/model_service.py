import torch
import cv2
import easyocr
import numpy as np
from pathlib import Path
from transformers import AutoTokenizer

from core.architectures.dual_stream_ner import DualStreamFusionNER
from scripts.data_preparation.preprocess_ocr import deskew
from schemas.predict import EntitySchema

def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")

class ModelService:
    def __init__(self):
        self.device = get_device()
        self.tokenizer = AutoTokenizer.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")
        self.unique_tags = ['O', 'B-PATIENT_AGE', 'B-SIGNATURE', 'I-PATIENT_NAME', 'I-CLINIC_NAME', 
                            'B-CLINIC_NAME', 'B-DATE', 'I-MEDICATIONS', 'B-PATIENT_NAME', 
                            'B-CLINIC_ADDRESS', 'B-MEDICATIONS', 'I-CLINIC_ADDRESS', 'I-SIGNATURE']
        self.id2tag = {i: tag for i, tag in enumerate(self.unique_tags)}
        
        self.model = None
        self.reader = None
        self._load_model()
        self._load_ocr()

    def _load_model(self):
        base_dir = Path(__file__).resolve().parent.parent
        weights_path = base_dir / 'models' / 'saved_weights' / 'dual_stream_ner_best.pth'
        
        if not weights_path.exists():
            print(f"Warning: Model weights missing at {weights_path}")
            return
            
        self.model = DualStreamFusionNER(bert_hidden_size=768, num_classes=len(self.unique_tags))
        checkpoint = torch.load(weights_path, map_location=self.device)
        state_dict = checkpoint.get('model_state_dict', checkpoint)
        new_state_dict = {k[7:] if k.startswith('module.') else k: v for k, v in state_dict.items()}
        self.model.load_state_dict(new_state_dict)
        self.model.to(self.device)
        self.model.eval()

    def _load_ocr(self):
        self.reader = easyocr.Reader(['en'], gpu=(self.device.type != 'cpu'))
        
    def is_ready(self):
        return self.model is not None and self.reader is not None

    def _preprocess_image(self, image_np):
        gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        deskewed = deskew(thresh)
        return cv2.bitwise_not(deskewed)

    def extract_from_text(self, text: str) -> list[EntitySchema]:
        vision_meta = [0.0, 0.0, 0.0, 0.0, 0.0]
        return self._run_inference(text, vision_meta)

    def extract_from_image(self, image_np: np.ndarray) -> tuple[str, list[EntitySchema]]:
        preprocessed = self._preprocess_image(image_np)
        results = self.reader.readtext(preprocessed)
        
        if not results:
            return "", []
            
        ocr_features = []
        for bbox, text, conf in results:
            ocr_features.append({
                "bbox": [[int(coord[0]), int(coord[1])] for coord in bbox],
                "confidence": float(conf)
            })
            
        full_text = " ".join([res[1] for res in results])
        
        avg_conf = sum([f['confidence'] for f in ocr_features]) / len(ocr_features)
        x1 = sum([f['bbox'][0][0] for f in ocr_features]) / len(ocr_features)
        y1 = sum([f['bbox'][0][1] for f in ocr_features]) / len(ocr_features)
        x2 = sum([f['bbox'][2][0] for f in ocr_features]) / len(ocr_features)
        y2 = sum([f['bbox'][2][1] for f in ocr_features]) / len(ocr_features)
        
        vision_meta = [avg_conf, x1, y1, x2, y2]
        entities = self._run_inference(full_text, vision_meta)
        
        return full_text, entities

    def _run_inference(self, text: str, vision_meta: list) -> list[EntitySchema]:
        if not self.is_ready():
            raise RuntimeError("Model is not loaded.")
            
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
            probs = torch.softmax(logits, dim=2)
            max_probs, predictions = torch.max(probs, dim=2)
            
            predictions = predictions[0].cpu().numpy()
            max_probs = max_probs[0].cpu().numpy()
            
        word_ids = encoding.word_ids()
        
        extracted = []
        previous_word_idx = None
        for i, word_idx in enumerate(word_ids):
            if word_idx is None or word_idx == previous_word_idx:
                continue
                
            tag_id = predictions[i]
            tag = self.id2tag[tag_id]
            conf = float(max_probs[i])
            
            if tag != 'O':
                extracted.append(EntitySchema(word=tokens[word_idx], tag=tag, confidence=conf))
                
            previous_word_idx = word_idx
            
        return extracted

# Singleton instance
model_service = ModelService()
