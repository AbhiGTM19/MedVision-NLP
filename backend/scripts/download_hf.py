#!/usr/env/bin python3
import os
from huggingface_hub import snapshot_download

datasets = [
    "ekacare/medical_records_parsing_validation_set",
    "chinmays18/medical-prescription-dataset",
    "avi-kai/Medical_Prescription_Handwritten_Words"
]

# Ensure working directory is set correctly
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw_dir = os.path.join(base_dir, "dataset", "raw")
os.makedirs(raw_dir, exist_ok=True)

for ds in datasets:
    repo_name = ds.split('/')[-1]
    local_dir = os.path.join(raw_dir, repo_name)
    print(f"Downloading {ds} to {local_dir}...")
    snapshot_download(repo_id=ds, repo_type="dataset", local_dir=local_dir)
    print(f"✅ Successfully downloaded {repo_name}!\n")
