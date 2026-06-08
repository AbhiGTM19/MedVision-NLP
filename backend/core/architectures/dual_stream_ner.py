import torch
import torch.nn as nn
from transformers import AutoModel

class DualStreamFusionNER(nn.Module):
    def __init__(self, bert_hidden_size=768, num_classes=13, bert_model_name="emilyalsentzer/Bio_ClinicalBERT"):
        super(DualStreamFusionNER, self).__init__()
        
        # Stream B: The raw NLP Engine directly inside the network (End-to-End)
        self.bert = AutoModel.from_pretrained(bert_model_name)
        
        # Stream A: Vision Metadata processing (5 variables: conf, x1, y1, x2, y2)
        self.vision_projection = nn.Linear(5, 128)
        self.vision_activation = nn.ReLU()
        
        # Late Fusion Projection (768 + 128 = 896 -> 256)
        self.fusion_projection = nn.Linear(bert_hidden_size + 128, 256)
        
        # Bottleneck Skip Connection (768 -> 256)
        self.nlp_skip = nn.Linear(bert_hidden_size, 256)
        
        self.fusion_activation = nn.ReLU()
        
        # MLOps Overfitting Protection: Dropout layer
        self.dropout = nn.Dropout(p=0.3)
        
        # Token-Level Classification Head
        self.classifier = nn.Linear(256, num_classes)
        
    def forward(self, input_ids, attention_mask, vision_meta):
        # 1. NLP Stream (End-to-End sequence extraction)
        # BERT output shape: (batch_size, seq_len, 768)
        bert_outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        nlp_out = bert_outputs.last_hidden_state
        
        # 2. Vision Stream (batch_size, 5) -> (batch_size, 128)
        vis_out = self.vision_projection(vision_meta)
        vis_out = self.vision_activation(vis_out)
        
        # Broadcast Vision Metadata across the Sequence Length
        # (batch_size, 128) -> (batch_size, 1, 128) -> (batch_size, seq_len, 128)
        batch_size, seq_len, _ = nlp_out.size()
        vis_out_expanded = vis_out.unsqueeze(1).expand(batch_size, seq_len, -1)
        
        # 3. Late Fusion: Concatenate along feature dimension
        # (batch_size, seq_len, 768 + 128 = 896)
        fused = torch.cat((nlp_out, vis_out_expanded), dim=2)
        fused = self.fusion_projection(fused)
        
        # 4. Residual Skip Connection (Preserving semantic fidelity)
        nlp_residual = self.nlp_skip(nlp_out)
        fused = fused + nlp_residual
        
        fused = self.fusion_activation(fused)
        
        # Apply Dropout to prevent Memorization/Overfitting
        fused = self.dropout(fused)
        
        # 5. Token Classification
        # Output shape: (batch_size, seq_len, num_classes)
        logits = self.classifier(fused)
        return logits
