from services.knowledge_service import knowledge_service
results = knowledge_service.retrieve_context("HTN", top_k=2)
for i, r in enumerate(results):
    print(f"--- Chunk {i} ---")
    print(r.content)
