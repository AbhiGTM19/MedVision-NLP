
from huggingface_hub import HfApi

# Your Hugging Face Repo ID
REPO_ID = "abhshkgtm19/medvision-models"
MODEL_FILE = "models/bio_clinicalBERT/bio_clinicalBERT_model.pth"
CONFIG_FILE = "models/bio_clinicalBERT/config.json"

# Get the token from user input securely
token = input("Enter your Hugging Face WRITE token (from https://huggingface.co/settings/tokens): ").strip()

api = HfApi(token=token)

print(f"\nUploading {MODEL_FILE} to {REPO_ID}...")

try:
    print(f"Uploading {MODEL_FILE}...")
    api.upload_file(
        path_or_fileobj=MODEL_FILE,
        path_in_repo="bio_clinicalBERT_model.pth",
        repo_id=REPO_ID,
        repo_type="model",
    )
    
    print(f"Uploading {CONFIG_FILE}...")
    api.upload_file(
        path_or_fileobj=CONFIG_FILE,
        path_in_repo="config.json",
        repo_id=REPO_ID,
        repo_type="model",
    )
    print("✅ Upload successful! Both model weights and config are now available on Hugging Face.")
except Exception as e:
    print(f"❌ Upload failed: {e}")
