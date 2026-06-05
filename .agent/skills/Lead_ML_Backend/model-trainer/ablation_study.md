# Comprehensive Ablation Study: Movie Review Sentiment Classifier

**Context:** This document summarizes the ablation study conducted for the Sentiment Prediction model. The study is divided into establishing the baseline and exploring advanced transformer architectures.

## Part I: Primary Modality Ablation
This phase establishes the baseline predictive power using classical NLP vs. modern deep learning.

| Phase | Model | Description | Test Accuracy |
| :---: | :--- | :--- | :--- |
| **Baseline** | `sklearn_sgd` | TF-IDF Vectorization + SGDClassifier baseline. | TBD |
| **Transformer** | `distilbert_base` | Fine-tuned DistilBERT via `train_transformer.py`. | TBD |

## Part II: Extended Architectural Ablation
Focuses on hyperparameter optimization and handling text length bottlenecks (e.g., reviews > 512 tokens).

### The Architectures Evaluated
#### A. Truncation Strategies
- **Mechanism:** Standard `max_length=512` truncation vs. Head+Tail truncation.

#### B. Ensemble Fusion
- **Mechanism:** Soft-voting ensemble combining the TF-IDF SGDClassifier probabilities with the Transformer logits.

### Extended HPO Results & Metrics
| Model Architecture | Fusion Strategy | Best HPO Params | Test Accuracy |
| :--- | :--- | :--- | :--- |
| `distilbert_base` | None | LR=2e-5, Batch=16 | TBD |
| `ensemble_sgd_bert` | Soft-Voting | N/A | TBD |

## Final Conclusions & Thesis Justifications
*(To be populated as experimental training runs via MLflow are completed).*
