import json
import logging
import sys
from pathlib import Path

import requests
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Add backend directory to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.knowledge_service import knowledge_service

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge"

def fetch_openfda_drugs(limit=20):
    """Fetch a sample of drug labels from OpenFDA"""
    logger.info(f"Fetching {limit} drug labels from OpenFDA...")
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
        logger.info(f"Successfully fetched {len(drugs)} drug records.")
        return drugs
    except Exception as e:
        logger.error(f"Error fetching from OpenFDA: {e}")
        return []

def ingest_abbreviations():
    abbv_file = DATA_DIR / "abbreviations.json"
    if not abbv_file.exists():
        logger.warning("Abbreviations file not found.")
        return []
        
    with open(abbv_file, "r") as f:
        data = json.load(f)
        
    documents = []
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
    logger.info(f"Processed {len(documents)} abbreviation chunks.")
    return documents

def ingest_guidelines():
    specialties_dir = DATA_DIR / "specialties"
    if not specialties_dir.exists():
        logger.warning("Specialties directory not found.")
        return []
        
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
        
    documents = []
    for file_path in specialties_dir.glob("*.md"):
        specialty_name = file_path.stem
        with open(file_path, "r") as f:
            content = f.read()
            
        chunks = text_splitter.split_text(content)
        
        for chunk in chunks:
            documents.append({
                "content": chunk,
                "metadata": {
                    "source": f"Local Guidelines - {specialty_name}",
                    "document_type": "guideline",
                    "specialty": specialty_name
                }
            })
    logger.info(f"Processed {len(documents)} guideline chunks using RecursiveCharacterTextSplitter.")
    return documents

def main():
    if not knowledge_service.collection:
        logger.error("KnowledgeService failed to initialize. Cannot ingest.")
        return
        
    logger.info("Starting Knowledge Ingestion...")
    all_docs = []
    
    all_docs.extend(fetch_openfda_drugs())
    all_docs.extend(ingest_abbreviations())
    all_docs.extend(ingest_guidelines())
    
    if not all_docs:
        logger.warning("No documents to ingest.")
        return
        
    logger.info(f"Ingesting {len(all_docs)} documents into ChromaDB...")
    
    texts = [doc["content"] for doc in all_docs]
    metadatas = [doc["metadata"] for doc in all_docs]
    ids = [f"doc_{i}" for i in range(len(all_docs))]
    
    knowledge_service.collection.upsert(
        documents=texts,
        metadatas=metadatas,
        ids=ids
    )
    
    logger.info("Ingestion complete!")
    logger.info(f"Total documents in DB: {knowledge_service.collection.count()}")

if __name__ == "__main__":
    main()
