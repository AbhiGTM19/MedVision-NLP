import pytest
from services.knowledge_service import knowledge_service

def test_knowledge_service_initialized():
    assert knowledge_service.collection is not None

def test_knowledge_retrieval():
    # We should be able to retrieve "Hypertension" since it was ingested from Abbreviations and Cardiology
    results = knowledge_service.retrieve_context("HTN", top_k=2)
    assert len(results) > 0
    assert any("Hypertension" in chunk.content or "HTN" in chunk.content for chunk in results)
