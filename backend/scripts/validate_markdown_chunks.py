import glob
import logging
import os

import pymupdf4llm
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def validate_extraction_and_chunking(sample_pdf_path: str, num_pages: int = 5):
    """
    Validates that pymupdf4llm and LangChain splitters correctly parse and chunk
    a medical PDF without creating empty chunks or dropping metadata.
    """
    if not os.path.exists(sample_pdf_path):
        logger.error(f"Sample PDF not found at {sample_pdf_path}")
        return False
        
    logger.info(f"Validating extraction on: {os.path.basename(sample_pdf_path)} (First {num_pages} pages)")
    
    try:
        # Step 1: Extract Markdown using PyMuPDF4LLM
        # We only extract a few pages to make the validation fast
        md_text = pymupdf4llm.to_markdown(sample_pdf_path, pages=list(range(num_pages)))
        
        if not md_text or len(md_text.strip()) == 0:
            logger.error("Extraction yielded empty markdown text!")
            return False
            
        logger.info(f"Successfully extracted {len(md_text)} characters of Markdown.")
        
        # Step 2: Markdown Header Splitting
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
        
        md_splits = markdown_splitter.split_text(md_text)
        logger.info(f"Markdown Splitter produced {len(md_splits)} logical chunks.")
        
        if len(md_splits) == 0:
            logger.error("Markdown Header Splitter failed to produce any chunks.")
            return False
            
        # Step 3: Recursive Character Splitting (for chunks that are still too large)
        chunk_size = 1000
        chunk_overlap = 200
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        
        final_splits = text_splitter.split_documents(md_splits)
        logger.info(f"Recursive Splitter produced a final total of {len(final_splits)} chunks.")
        
        # Step 4: Validation Assertions
        empty_chunks = 0
        oversized_chunks = 0
        
        for i, split in enumerate(final_splits):
            if not split.page_content or len(split.page_content.strip()) == 0:
                empty_chunks += 1
            if len(split.page_content) > chunk_size * 1.5:  # Tolerance
                oversized_chunks += 1
                
        if empty_chunks > 0:
            logger.error(f"Validation Failed: Found {empty_chunks} completely empty chunks!")
            return False
            
        if oversized_chunks > 0:
            logger.warning(f"Validation Warning: Found {oversized_chunks} chunks larger than target size.")
            
        logger.info("✅ DATA INTEGRITY VALIDATION PASSED!")
        
        # Print a sample chunk to verify metadata
        if final_splits:
            sample = final_splits[min(2, len(final_splits)-1)]
            logger.info("\n--- SAMPLE CHUNK METADATA ---")
            logger.info(sample.metadata)
            logger.info("--- SAMPLE CHUNK CONTENT ---")
            logger.info(sample.page_content[:200] + "...")
            
        return True

    except Exception as e:
        logger.error(f"Validation threw an exception: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    knowledge_dir = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge")
    pdf_files = glob.glob(f"{knowledge_dir}/**/*.pdf", recursive=True)
    
    if not pdf_files:
        logger.error("No PDFs found in backend/data/knowledge to test.")
    else:
        # Just grab the first PDF we find for validation
        sample_pdf = pdf_files[0]
        validate_extraction_and_chunking(sample_pdf)
