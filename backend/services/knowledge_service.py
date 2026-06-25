import logging
from pathlib import Path

import chromadb
import chromadb.utils.embedding_functions as embedding_functions

from core.config import settings
from schemas.knowledge import RetrievedChunk

logger = logging.getLogger(__name__)

CHROMA_DB_PATH = Path(settings.STORAGE_PATH)

class KnowledgeService:
    def __init__(self):
        self.chroma_client = None
        self.collection = None
        self._init_db()

    def _init_db(self):
        try:
            CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)
            logger.info(f"Initializing ChromaDB at path: {CHROMA_DB_PATH}")
            sqlite_path = CHROMA_DB_PATH / "chroma.sqlite3"
            if sqlite_path.exists():
                logger.info(f"Found chroma.sqlite3! Size: {sqlite_path.stat().st_size} bytes")
            else:
                logger.warning(f"chroma.sqlite3 NOT FOUND at {sqlite_path}! (It may be created fresh)")
                
            self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
            
            # Using sentence-transformers for local fast embeddings
            emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
            
            self.collection = self.chroma_client.get_or_create_collection(
                name="medvision_knowledge",
                embedding_function=emb_fn
            )
            
            doc_count = self.collection.count()
            logger.info(f"ChromaDB initialized successfully. Collection 'medvision_knowledge' contains {doc_count} documents.")
            
            if doc_count == 0:
                logger.error("CRITICAL: ChromaDB collection is empty! The RAG will return N/A.")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}", exc_info=True)

    def retrieve_context(self, query_text: str, specialty: str | None = None, top_k: int = 5) -> list[RetrievedChunk]:
        if not self.collection:
            logger.warning("Retrieval attempted but ChromaDB collection is not initialized.")
            return []
            
        # Advanced Retrieval: Fetch more candidates (e.g. 3x) for post-retrieval re-sorting
        fetch_k = top_k * 3
        
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=fetch_k
            )
            
            chunks = []
            if results["documents"] and len(results["documents"]) > 0:
                docs = results["documents"][0]
                metadatas = results["metadatas"][0]
                distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)
                
                for doc, meta, dist in zip(docs, metadatas, distances):
                    chunks.append(RetrievedChunk(
                        content=doc,
                        source=meta.get("source", "Unknown"),
                        specialty=meta.get("specialty"),
                        document_type=meta.get("document_type", "Unknown"),
                        layer=meta.get("layer", "foundation"),
                        relevance_score=float(dist)
                    ))
                    
            # Chunk Re-sorting: Boost relevance if layer == "action"
            # L2 distance means lower is better, so multiplying by 0.5 boosts its ranking
            for c in chunks:
                if c.layer == "action":
                    c.relevance_score *= 0.5
                    
            # Secondary Chunk Re-sorting: Boost relevance if metadata specialty matches the predicted specialty
            if specialty:
                query_spec_lower = specialty.lower()
                for c in chunks:
                    if c.specialty and (query_spec_lower in c.specialty.lower() or c.specialty.lower() in query_spec_lower):
                        c.relevance_score *= 0.8
                        
            # Re-sort by the adjusted relevance score
            chunks.sort(key=lambda x: x.relevance_score)
            
            # Return only the top_k requested
            return chunks[:top_k]
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}", exc_info=True)
            return []

knowledge_service = KnowledgeService()
