import os
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
from pathlib import Path
import io

from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoConfig
from huggingface_hub import hf_hub_download
import pytesseract
from captum.attr import LayerIntegratedGradients

from schemas.predict import WordAttribution

def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")

class ModelService:
    def __init__(self):
        self.device = get_device()
        self.base_dir = Path(__file__).resolve().parent.parent
        self.models_dir = self.base_dir / "models"
        self.bert_dir = self.models_dir / "bio_clinicalBERT"
        
        self.bert_model = None
        self.bert_tokenizer = None
        self.bert_config = None
        self.lig = None
        
        self._load_models()

    def _load_models(self):
        # 1. Load Bio_ClinicalBERT
        try:
            self.bert_config = AutoConfig.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")
            self.bert_tokenizer = AutoTokenizer.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")
            self.bert_model = AutoModelForSequenceClassification.from_config(self.bert_config)
            
            # Ensure directory exists
            self.bert_dir.mkdir(parents=True, exist_ok=True)
            bert_pth_path = self.bert_dir / "bio_clinicalBERT_model.pth"
            
            # Dynamic Runtime Download for Production (from HF Model Hub)
            if os.environ.get("ENV") == "prod" and not bert_pth_path.exists():
                hf_model_repo = os.environ.get("HF_MODEL_REPO", "abhshkgtm19/medvision-models")
                print(f"Production environment detected. Downloading missing weights from HF Hub: {hf_model_repo}...")
                try:
                    # Download directly into the local models directory
                    downloaded_path = hf_hub_download(
                        repo_id=hf_model_repo, 
                        filename="bio_clinicalBERT_model.pth", 
                        local_dir=str(self.bert_dir)
                    )
                    print(f"Successfully downloaded weights to {downloaded_path}")
                except Exception as e:
                    print(f"Warning: Failed to download weights from HF. Ensure repo exists and is public. Error: {e}")
            elif not bert_pth_path.exists():
                 print(f"Warning: Local model weights not found at {bert_pth_path}. Ensure you have fine-tuned the model locally.")
            
            if bert_pth_path.exists():
                self.bert_model.load_state_dict(torch.load(bert_pth_path, map_location=self.device, weights_only=True))
            else:
                print("Falling back to un-finetuned HuggingFace weights.")
                self.bert_model = AutoModelForSequenceClassification.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")
                
            self.bert_model.to(self.device)
            self.bert_model.eval()
            
            # Setup Captum XAI for BERT embeddings
            self.lig = LayerIntegratedGradients(self._bert_forward, self.bert_model.bert.embeddings.word_embeddings)
            print("Bio_ClinicalBERT loaded successfully.")
        except Exception as e:
            print(f"Failed to load Bio_ClinicalBERT: {e}")

    def is_ready(self):
        return self.bert_model is not None

    def _bert_forward(self, input_ids):
        # Captum expects a function that takes inputs and returns the target output
        attention_mask = (input_ids != self.bert_tokenizer.pad_token_id).long()
        return self.bert_model(input_ids, attention_mask=attention_mask).logits

    def extract_from_text(self, text: str) -> tuple[str, float, list[WordAttribution]]:
        if not self.is_ready():
            raise RuntimeError("Models are not fully loaded.")
            
        if not text.strip():
            return "Unknown", 0.0, []

        # 1. Prediction
        inputs = self.bert_tokenizer(text, return_tensors="pt", padding="max_length", max_length=512, truncation=True).to(self.device)
        input_ids = inputs["input_ids"]
        
        with torch.no_grad():
            outputs = self.bert_model(**inputs)
            probs = F.softmax(outputs.logits, dim=-1)
            confidence, predicted_class_id = torch.max(probs, dim=-1)
            
            confidence = confidence.item()
            predicted_class_id = predicted_class_id.item()
            predicted_specialty = self.bert_config.id2label[predicted_class_id]

        # 2. XAI / Feature Attribution (Captum)
        word_attributions = []
        try:
            # Generate attributions for the predicted class
            # Strip padded tokens for faster computation
            seq_len = (input_ids != self.bert_tokenizer.pad_token_id).sum().item()
            short_input_ids = input_ids[:, :seq_len]
            
            attributions, delta = self.lig.attribute(inputs=short_input_ids, 
                                                     target=predicted_class_id, 
                                                     return_convergence_delta=True)
            
            # Summarize the attributions across the embedding dimension
            attributions_sum = attributions.sum(dim=-1).squeeze(0)
            
            # Normalize
            norm = torch.norm(attributions_sum)
            if norm > 0:
                attributions_sum = attributions_sum / norm
            
            tokens = self.bert_tokenizer.convert_ids_to_tokens(short_input_ids[0])
            
            current_word = ""
            current_attr = 0.0
            
            for token, attr in zip(tokens, attributions_sum.cpu().tolist()):
                if token in [self.bert_tokenizer.cls_token, self.bert_tokenizer.sep_token]:
                    continue
                    
                if token.startswith("##"):
                    current_word += token[2:]
                    current_attr += attr
                else:
                    if current_word:
                        word_attributions.append(WordAttribution(word=current_word, score=current_attr))
                    current_word = token
                    current_attr = attr
                    
            if current_word:
                word_attributions.append(WordAttribution(word=current_word, score=current_attr))
                
        except Exception as e:
            print(f"XAI calculation failed: {e}")
            
        return predicted_specialty, confidence, word_attributions

    def extract_from_image(self, image_bytes: bytes) -> tuple[str, str, float, list[WordAttribution]]:
        if not self.is_ready():
            raise RuntimeError("Models are not fully loaded.")
            
        # 1. Image loading
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # 2. Tesseract OCR extraction
        extracted_text = pytesseract.image_to_string(image).strip()
        
        if not extracted_text:
            return "", "Unknown", 0.0, []
            
        # 3. Text classification and XAI
        specialty, conf, attributions = self.extract_from_text(extracted_text)
        
        return extracted_text, specialty, conf, attributions

# Singleton instance
model_service = ModelService()
