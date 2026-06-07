import torch
import torch.nn as nn

class DualStreamFusionNER(nn.Module):
    def __init__(self, bert_hidden_size=768, num_classes=10):
        super(DualStreamFusionNER, self).__init__()
        
        # Stream A (Vision Metadata)
        # We take: 1 (avg_confidence) + 4 (avg bbox x1,y1,x2,y2) = 5 features
        self.vision_fc = nn.Sequential(
            nn.Linear(5, 32),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        
        # Stream B (NLP Embeddings)
        self.nlp_fc = nn.Sequential(
            nn.Linear(bert_hidden_size, 256),
            nn.ReLU(),
            nn.Dropout(0.3)
        )
        
        # Late Fusion Layer
        # Concatenate 32 (Vision) + 256 (NLP) = 288 dimensions
        self.fusion_classifier = nn.Sequential(
            nn.Linear(288, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            # Outputting logits for entity classes (e.g., Drug, Disease, Dosage presence)
            nn.Linear(128, num_classes)
        )
        
    def forward(self, nlp_embeddings, vision_metadata):
        """
        Args:
            nlp_embeddings: Tensor of shape (batch_size, 768)
            vision_metadata: Tensor of shape (batch_size, 5) 
                             (e.g., avg_confidence, avg_x1, avg_y1, avg_x2, avg_y2)
        """
        # Process streams independently
        nlp_out = self.nlp_fc(nlp_embeddings)
        
        # Q2 Fix: To prevent data loss during compression, we can add a Residual/Skip Connection
        # We project the original 768d vector to 256d and add it to the output
        # (Alternatively, we can use an auxiliary loss during training)
        projected_nlp = nlp_embeddings[:, :256] # Simplified projection by slicing, or use a linear layer
        nlp_out = nlp_out + projected_nlp
        
        vision_out = self.vision_fc(vision_metadata)
        
        # Late Fusion: Concatenate along feature dimension
        fused_vector = torch.cat((nlp_out, vision_out), dim=1)
        
        # Final Classification
        logits = self.fusion_classifier(fused_vector)
        return logits

# Example usage/test
if __name__ == "__main__":
    model = DualStreamFusionNER(num_classes=3)
    
    # Mock data: Batch of 2 documents
    mock_bert = torch.rand(2, 768)
    # Mock vision metadata: [avg_conf, x1, y1, x2, y2]
    mock_vision = torch.tensor([
        [0.95, 10.0, 20.0, 100.0, 40.0],
        [0.40, 15.0, 25.0, 105.0, 45.0]
    ])
    
    output = model(mock_bert, mock_vision)
    print("Dual Stream Fusion Model Output Logits:", output.shape)
    # Expected shape: [2, 3] (Batch Size, Num Classes)
