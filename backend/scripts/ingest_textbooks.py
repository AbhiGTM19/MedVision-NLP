import glob
import logging
import os
from typing import List

import pymupdf4llm
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# List of filenames or substrings that identify an Indian "Action" layer textbook
ACTION_LAYER_IDENTIFIERS = [
    "api-textbook",
    "bedside-clinics",
    "ghai-essential-pediatrics",
    "dc-duttas",
    "National Formulary of India",
    "Essentals of Medical Pharmacology" # KD Tripathi
]

def determine_layer(filename: str) -> str:
    """Returns 'action' for Indian textbooks, 'foundation' for everything else."""
    for identifier in ACTION_LAYER_IDENTIFIERS:
        if identifier.lower() in filename.lower():
            return "action"
    return "foundation"

def ingest_all_pdfs():
    knowledge_dir = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge")
    persist_dir = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
    
    # Ensure directories exist
    os.makedirs(persist_dir, exist_ok=True)
    
    # Find all PDFs
    pdf_files = glob.glob(f"{knowledge_dir}/**/*.pdf", recursive=True)
    if not pdf_files:
        logger.error(f"No PDFs found in {knowledge_dir}")
        return

    # Initialize ChromaDB Client
    logger.info("Initializing ChromaDB and Embedding Model (all-MiniLM-L6-v2)...")
    # Using a fast, local HuggingFace embedding model for ingestion
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    vectorstore = Chroma(
        collection_name="medvision_knowledge",
        embedding_function=embeddings,
        persist_directory=persist_dir
    )

    # Initialize splitters
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False
    )
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        layer = determine_layer(filename)
        logger.info(f"Processing: {filename} (Layer: {layer})")
        
        try:
            # 1. Extract Markdown
            logger.info("  -> Extracting Markdown...")
            # For massive books, we would chunk this by page ranges to avoid OOM,
            # but for this script we will parse the whole document.
            md_text = pymupdf4llm.to_markdown(pdf_path, use_ocr=False)
            
            if not md_text:
                logger.warning(f"  -> Skipping {filename}, no text extracted.")
                continue
                
            # 2. Split by Headers
            logger.info("  -> Chunking by Markdown headers...")
            header_splits = markdown_splitter.split_text(md_text)
            
            # 3. Recursive Split
            logger.info("  -> Applying Recursive Character splitting...")
            final_splits = text_splitter.split_documents(header_splits)
            
            # 4. Inject Metadata
            valid_splits: List[Document] = []
            for split in final_splits:
                if split.page_content and len(split.page_content.strip()) > 0:
                    # Inject our custom metadata
                    split.metadata["source"] = filename
                    split.metadata["layer"] = layer
                    valid_splits.append(split)
                    
            logger.info(f"  -> Generated {len(valid_splits)} valid chunks.")
            
            # 5. Ingest to ChromaDB
            # Add in batches of 5000 to prevent SQLite errors
            batch_size = 5000
            for i in range(0, len(valid_splits), batch_size):
                batch = valid_splits[i:i + batch_size]
                vectorstore.add_documents(documents=batch)
            
            logger.info(f"✅ Successfully ingested {filename}")
            
        except Exception as e:
            logger.error(f"❌ Failed to process {filename}: {e}", exc_info=True)

    logger.info(f"🎉 Ingestion Complete! Database persisted at {persist_dir}")

if __name__ == "__main__":
    ingest_all_pdfs()
