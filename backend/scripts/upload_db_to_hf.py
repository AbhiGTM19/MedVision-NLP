import os

from huggingface_hub import HfApi


def upload_database():
    api = HfApi()
    
    # We create a dedicated dataset for the database
    dataset_id = "abhshkgtm19/MedVision-DB"
    
    print(f"🚀 Creating private Hugging Face Dataset: {dataset_id}")
    try:
        api.create_repo(repo_id=dataset_id, repo_type="dataset", private=True, exist_ok=True)
    except Exception as e:
        print(f"Note: {e}")

    local_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db"))
    
    print(f"📦 Uploading Vector Database from {local_db_path} to {dataset_id}...")
    try:
        api.upload_folder(
            folder_path=local_db_path,
            repo_id=dataset_id,
            repo_type="dataset",
            path_in_repo="."
        )
        print("✅ Successfully uploaded database to Hugging Face Dataset!")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        print("\nPlease ensure you are logged in to Hugging Face locally by running:")
        print("huggingface-cli login")

if __name__ == "__main__":
    upload_database()
