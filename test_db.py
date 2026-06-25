import chromadb
from pathlib import Path
db_path = str(Path("/Users/abhi/Downloads/AI ML/MedVision-NLP/backend/data/chroma_db").resolve())
print(f"Connecting to: {db_path}")
client = chromadb.PersistentClient(path=db_path)
try:
    collection = client.get_collection("medvision_knowledge")
    print(f"Count: {collection.count()}")
    results = collection.get(limit=1)
    if results['metadatas']:
        print(f"Metadata: {results['metadatas'][0]}")
except Exception as e:
    print(f"Error: {e}")
