import pytest
from unittest.mock import MagicMock, patch

from services.llm_service import LLMService
from schemas.predict import ChatMessage

@pytest.fixture
def mock_llm_service():
    with patch("services.llm_service.genai.Client") as mock_client:
        with patch("services.llm_service.settings") as mock_settings:
            mock_settings.GOOGLE_API_KEY = "fake_key"
            service = LLMService()
            yield service

def test_generate_chat_response_with_key(mock_llm_service):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.text = "This is a mock response."
    mock_llm_service.client.models.generate_content.return_value = mock_response

    messages = [ChatMessage(role="user", content="Hello")]
    response = mock_llm_service.generate_chat_response(messages)

    assert response == "This is a mock response."
    mock_llm_service.client.models.generate_content.assert_called_once()

def test_generate_rag_response_with_key(mock_llm_service):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.text = "This is a mock RAG answer."
    mock_llm_service.client.models.generate_content.return_value = mock_response

    # We mock knowledge service as well
    with patch("services.llm_service.knowledge_service.retrieve_context") as mock_retrieve:
        mock_retrieve.return_value = [] # Empty chunks for simplicity
        
        rag_response = mock_llm_service.generate_rag_response("What is HTN?")
        
        assert rag_response.answer == "This is a mock RAG answer."
        assert isinstance(rag_response.sources, list)

def test_llm_service_no_key():
    with patch("services.llm_service.os.getenv", return_value=None):
        with patch("services.llm_service.settings") as mock_settings:
            mock_settings.GOOGLE_API_KEY = None
            service = LLMService()
            
            rag_resp = service.generate_rag_response("test")
            assert "disabled" in rag_resp.answer
            
            chat_resp = service.generate_chat_response([])
            assert "configured" in chat_resp
