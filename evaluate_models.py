import os
import random
import time

from sklearn.metrics import accuracy_score, precision_recall_fscore_support

# Suppress Hugging Face warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from services.model_service import model_service


def load_test_data(sample_size=500):
    """Load a random sample of pos and neg reviews from the test set."""
    base_dir = "dataset/aclImdb/test"
    reviews = []
    labels = []
    
    print(f"Loading {sample_size * 2} random test samples...")
    
    for label, folder in [(1, 'pos'), (0, 'neg')]:
        folder_path = os.path.join(base_dir, folder)
        if not os.path.exists(folder_path):
            print(f"Error: Could not find dataset folder: {folder_path}")
            return [], []
            
        all_files = os.listdir(folder_path)
        sampled_files = random.sample(all_files, min(sample_size, len(all_files)))
        
        for filename in sampled_files:
            with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as f:
                reviews.append(f.read())
                labels.append(label)
                
    return reviews, labels

def evaluate_models():
    reviews, true_labels = load_test_data(sample_size=500) # 1000 total samples
    if not reviews:
        return
        
    print("Evaluating Fast Model (SGDClassifier)...")
    fast_preds = []
    fast_start_time = time.time()
    for review in reviews:
        label, _, _ = model_service.predict_fast(review)
        fast_preds.append(1 if label == "positive" else 0)
    fast_end_time = time.time()
    
    print("Evaluating Deep Transformer (DistilBERT)...")
    accurate_preds = []
    accurate_start_time = time.time()
    for review in reviews:
        label, _, _ = model_service.predict_accurate(review)
        accurate_preds.append(1 if label == "positive" else 0)
    accurate_end_time = time.time()
    
    # Calculate metrics
    fast_acc = accuracy_score(true_labels, fast_preds)
    fast_p, fast_r, fast_f1, _ = precision_recall_fscore_support(true_labels, fast_preds, average='binary')
    fast_latency = (fast_end_time - fast_start_time) / len(reviews) * 1000 # ms
    
    acc_acc = accuracy_score(true_labels, accurate_preds)
    acc_p, acc_r, acc_f1, _ = precision_recall_fscore_support(true_labels, accurate_preds, average='binary')
    acc_latency = (accurate_end_time - accurate_start_time) / len(reviews) * 1000 # ms
    
    print("\n" + "="*40)
    print("🚀 FAST MODEL (SGDClassifier) METRICS")
    print("="*40)
    print(f"Accuracy:  {fast_acc*100:.2f}%")
    print(f"F1-Score:  {fast_f1*100:.2f}%")
    print(f"Latency:   {fast_latency:.2f} ms/sample")
    
    print("\n" + "="*40)
    print("🧠 DEEP TRANSFORMER (DistilBERT) METRICS")
    print("="*40)
    print(f"Accuracy:  {acc_acc*100:.2f}%")
    print(f"F1-Score:  {acc_f1*100:.2f}%")
    print(f"Latency:   {acc_latency:.2f} ms/sample")
    print("="*40)

if __name__ == "__main__":
    evaluate_models()
