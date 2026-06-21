import json
import os
import sys
import requests
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.knowledge_service import knowledge_service

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge"

def fetch_openfda_drugs(limit=20):
    """Fetch a sample of drug labels from OpenFDA"""
    print(f"Fetching {limit} drug labels from OpenFDA...")
    url = f"https://api.fda.gov/drug/label.json?limit={limit}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        drugs = []
        for item in results:
            # Extract basic info
            brand_name = item.get("openfda", {}).get("brand_name", ["Unknown"])[0]
            generic_name = item.get("openfda", {}).get("generic_name", ["Unknown"])[0]
            indications = item.get("indications_and_usage", [""])[0]
            warnings = item.get("warnings", [""])[0]
            
            if indications:
                content = f"Drug: {brand_name} ({generic_name})\nIndications: {indications}\nWarnings: {warnings}"
                drugs.append({
                    "content": content,
                    "metadata": {
                        "source": "OpenFDA",
                        "document_type": "drug",
                        "specialty": "General" # We could try to map this better
                    }
                })
        print(f"Successfully fetched {len(drugs)} drug records.")
        return drugs
    except Exception as e:
        print(f"Error fetching from OpenFDA: {e}")
        return []

def ingest_abbreviations():
    abbv_file = DATA_DIR / "abbreviations.json"
    if not abbv_file.exists():
        print("Abbreviations file not found.")
        return []
        
    with open(abbv_file, "r") as f:
        data = json.load(f)
        
    documents = []
    # We group abbreviations into chunks of 10 to avoid too many small documents
    items = list(data.items())
    chunk_size = 10
    
    for i in range(0, len(items), chunk_size):
        chunk = items[i:i+chunk_size]
        content = "Medical Abbreviations:\n" + "\n".join([f"- {k}: {v}" for k, v in chunk])
        documents.append({
            "content": content,
            "metadata": {
                "source": "Local Dataset",
                "document_type": "abbreviation",
                "specialty": "General"
            }
        })
    print(f"Processed {len(documents)} abbreviation chunks.")
    return documents

def ingest_guidelines():
    specialties_dir = DATA_DIR / "specialties"
    if not specialties_dir.exists():
        print("Specialties directory not found.")
        return []
        
    documents = []
    for file_path in specialties_dir.glob("*.md"):
        specialty_name = file_path.stem
        with open(file_path, "r") as f:
            content = f.read()
            
        # For simplicity, we chunk by H2 headings (##)
        sections = content.split("\n## ")
        
        # The first chunk might just be the title
        if sections:
            intro = sections[0].strip()
            if intro:
                documents.append({
                    "content": intro,
                    "metadata": {
                        "source": f"Local Guidelines - {specialty_name}",
                        "document_type": "guideline",
                        "specialty": specialty_name
                    }
                })
                
            for section in sections[1:]:
                section_content = "## " + section.strip()
                documents.append({
                    "content": section_content,
                    "metadata": {
                        "source": f"Local Guidelines - {specialty_name}",
                        "document_type": "guideline",
                        "specialty": specialty_name
                    }
                })
    print(f"Processed {len(documents)} guideline sections.")
    return documents

def main():
    if not knowledge_service.collection:
        print("KnowledgeService failed to initialize. Cannot ingest.")
        return
        
    print("Starting Knowledge Ingestion...")
    all_docs = []
    
    all_docs.extend(fetch_openfda_drugs())
    all_docs.extend(ingest_abbreviations())
    all_docs.extend(ingest_guidelines())
    
    if not all_docs:
        print("No documents to ingest.")
        return
        
    print(f"Ingesting {len(all_docs)} documents into ChromaDB...")
    
    texts = [doc["content"] for doc in all_docs]
    metadatas = [doc["metadata"] for doc in all_docs]
    ids = [f"doc_{i}" for i in range(len(all_docs))]
    
    knowledge_service.collection.upsert(
        documents=texts,
        metadatas=metadatas,
        ids=ids
    )
    
    print("Ingestion complete!")
    print(f"Total documents in DB: {knowledge_service.collection.count()}")

if __name__ == "__main__":
    main()
