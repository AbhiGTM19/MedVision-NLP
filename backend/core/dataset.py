import json
import torch
from torch.utils.data import Dataset

class FusedMedicalDataset(Dataset):
    def __init__(self, jsonl_path, tokenizer, max_length=512):
        self.records = []
        
        self.unique_tags = ['O', 'B-PATIENT_AGE', 'B-SIGNATURE', 'I-PATIENT_NAME', 'I-CLINIC_NAME', 
                            'B-CLINIC_NAME', 'B-DATE', 'I-MEDICATIONS', 'B-PATIENT_NAME', 
                            'B-CLINIC_ADDRESS', 'B-MEDICATIONS', 'I-CLINIC_ADDRESS', 'I-SIGNATURE']
        self.tag2id = {tag: i for i, tag in enumerate(self.unique_tags)}
        self.tag_counts = {tag: 0 for tag in self.unique_tags}
        
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                if 'tokens' in data and 'iob_tags' in data:
                    self.records.append(data)
                    for tag in data['iob_tags']:
                        if tag in self.tag_counts:
                            self.tag_counts[tag] += 1
                            
        self.tokenizer = tokenizer
        self.max_length = max_length
        
    def __len__(self):
        return len(self.records)
        
    def __getitem__(self, idx):
        record = self.records[idx]
        tokens = record['tokens']
        tags = record['iob_tags']
        
        # Tokenize with offsets to align IOB tags
        encoding = self.tokenizer(
            tokens, 
            is_split_into_words=True, 
            return_offsets_mapping=False, 
            padding='max_length', 
            truncation=True, 
            max_length=self.max_length
        )
        
        labels = []
        word_ids = encoding.word_ids()
        
        previous_word_idx = None
        for word_idx in word_ids:
            if word_idx is None:
                labels.append(-100) # Special tokens are masked with -100
            elif word_idx != previous_word_idx:
                tag = tags[word_idx] if word_idx < len(tags) else 'O'
                labels.append(self.tag2id.get(tag, self.tag2id['O']))
            else:
                labels.append(-100) # Subwords are masked with -100
            previous_word_idx = word_idx
            
        input_ids = torch.tensor(encoding['input_ids'], dtype=torch.long)
        attention_mask = torch.tensor(encoding['attention_mask'], dtype=torch.long)
        labels_tensor = torch.tensor(labels, dtype=torch.long)
        
        avg_conf = record.get('avg_ocr_confidence', 0.0)
        ocr_features = record.get('ocr_features', [])
        if ocr_features:
            x1 = sum([f['bbox'][0][0] for f in ocr_features]) / len(ocr_features)
            y1 = sum([f['bbox'][0][1] for f in ocr_features]) / len(ocr_features)
            x2 = sum([f['bbox'][2][0] for f in ocr_features]) / len(ocr_features)
            y2 = sum([f['bbox'][2][1] for f in ocr_features]) / len(ocr_features)
        else:
            x1, y1, x2, y2 = 0.0, 0.0, 0.0, 0.0
            
        vision_meta = torch.tensor([avg_conf, x1, y1, x2, y2], dtype=torch.float32)
        
        return input_ids, attention_mask, vision_meta, labels_tensor
