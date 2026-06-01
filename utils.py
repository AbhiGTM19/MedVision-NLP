import pickle
import os

def load_pickle_safe(path):
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as f:
        return pickle.load(f)

def load_transformer_safe(path):
    from transformers import pipeline
    if not os.path.exists(path):
        return None
    return pipeline("sentiment-analysis", model=path)