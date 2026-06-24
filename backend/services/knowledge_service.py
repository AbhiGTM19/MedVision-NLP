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
            self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
            
            # Using sentence-transformers for local fast embeddings
            emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
            
            self.collection = self.chroma_client.get_or_create_collection(
                name="medical_knowledge",
                embedding_function=emb_fn
            )
            logger.info("ChromaDB initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}", exc_info=True)

    def retrieve_context(self, query_text: str, specialty: str | None = None, top_k: int = 5) -> list[RetrievedChunk]:
        if not self.collection:
            logger.warning("Retrieval attempted but ChromaDB collection is not initialized.")
            return []
            
        # Advanced Retrieval: Fetch more candidates (e.g. 2x) for post-retrieval re-sorting
        fetch_k = top_k * 2
        
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
                        relevance_score=float(dist)
                    ))
                    
            # Chunk Re-sorting: Boost relevance if metadata specialty matches the predicted specialty
            if specialty:
                query_spec_lower = specialty.lower()
                for c in chunks:
                    if c.specialty and (query_spec_lower in c.specialty.lower() or c.specialty.lower() in query_spec_lower):
                        # Boost score (lower distance is better in ChromaDB L2 distance)
                        c.relevance_score *= 0.5 
                        
            # Re-sort by the adjusted relevance score
            chunks.sort(key=lambda x: x.relevance_score)
            
            # Return only the top_k requested
            return chunks[:top_k]
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}", exc_info=True)
            return []

knowledge_service = KnowledgeService()
