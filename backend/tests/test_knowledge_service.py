from unittest.mock import patch

import pytest

from services.knowledge_service import knowledge_service


def test_knowledge_service_initialized():
    assert knowledge_service.collection is not None

def test_knowledge_retrieval():
    if knowledge_service.collection.count() == 0:
        pytest.skip("ChromaDB is empty. Skipping retrieval test.")
        
    # We should be able to retrieve "Hypertension" since it was ingested from Abbreviations and Cardiology
    results = knowledge_service.retrieve_context("HTN", top_k=2)
    assert len(results) > 0
    assert any("Hypertension" in chunk.content or "HTN" in chunk.content for chunk in results)

def test_dual_layer_relevance_boosting():
    """
    Test that the retrieve_context function correctly prioritizes 
    'action' layer textbooks over 'foundation' layer.
    """
    # Create mock ChromaDB results where a foundation chunk actually has a 
    # slightly better (lower) native distance than the action chunk.
    mock_results = {
        "documents": [["Foundation text", "Action text"]],
        "metadatas": [[
            {"source": "Harrison's", "layer": "foundation"},
            {"source": "API Textbook", "layer": "action"}
        ]],
        "distances": [[0.3, 0.4]] # Foundation natively ranks higher (0.3 < 0.4)
    }
    
    with patch.object(knowledge_service.collection, 'query', return_value=mock_results):
        # We fetch top_k=2.
        results = knowledge_service.retrieve_context("mock query", top_k=2)
        
        assert len(results) == 2
        # After boosting, the action text's score (0.4 * 0.5 = 0.2) 
        # should beat the foundation text's score (0.3 * 1.0 = 0.3)
        assert results[0].layer == "action"
        assert results[0].relevance_score == 0.2
        assert results[1].layer == "foundation"
        assert results[1].relevance_score == 0.3
