import logging
from pathlib import Path

import chromadb
import chromadb.utils.embedding_functions as embedding_functions

from schemas.knowledge import RetrievedChunk

logger = logging.getLogger(__name__)

CHROMA_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "chroma_db"

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
            
        # We rely on semantic search instead of exact match metadata filtering 
        # because the model's predicted specialty (e.g., "Cardiovascular / Pulmonary") 
        # might not exactly match the ingested metadata (e.g., "Cardiology" or "General").
        where_filter = None
        
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=top_k,
                where=where_filter
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
            return chunks
        except Exception as e:
            logger.error(f"Retrieval failed: {e}", exc_info=True)
            return []

knowledge_service = KnowledgeService()
