import os

from huggingface_hub import HfApi


def deploy():
    print("🚀 Initiating secure deployment to Hugging Face Spaces...")
    api = HfApi()
    
    # The repository ID where the space is hosted
    repo_id = "abhshkgtm19/MedVision"
    
    # Get the root directory of the project
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    print(f"📦 Uploading workspace from: {root_dir}")
    print("🔒 Note: This uploads directly to Hugging Face via HTTPS, completely bypassing GitHub.")
    
    try:
        api.upload_folder(
            folder_path=root_dir,
            repo_id=repo_id,
            repo_type="space",
            # We explicitly allow chroma_db but ignore virtual environments and git history
            ignore_patterns=[
                ".git/*",
                ".github/*",
                "backend/.venv/*",
                "venv/*",
                "__pycache__/*",
                "*.pyc",
                "backend/models/tracking/*",
                ".env"
            ]
        )
        print("✅ Deployment successful! Your Space should now be rebuilding.")
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        print("\nPlease ensure you have logged in to Hugging Face locally by running:")
        print("huggingface-cli login")

if __name__ == "__main__":
    deploy()
