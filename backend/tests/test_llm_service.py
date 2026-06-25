from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from schemas.predict import ChatMessage
from services.llm_service import LLMService


@pytest.fixture
def mock_llm_service():
    with patch("services.llm_service.genai.Client"):
        with patch("services.llm_service.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = "fake_key"
            yield LLMService()

@pytest.mark.asyncio
async def test_generate_chat_response_stream_with_key(mock_llm_service):
    # Setup mock response
    mock_chunk = MagicMock()
    mock_chunk.text = "This is a mock response."
    
    async def mock_generate_content_stream(*args, **kwargs):
        yield mock_chunk

    mock_llm_service.client.aio.models.generate_content_stream = mock_generate_content_stream

    messages = [ChatMessage(role="user", content="Hello")]
    response_stream = mock_llm_service.generate_chat_response_stream(messages)
    
    responses = []
    async for r in response_stream:
        responses.append(r)

    assert any("This is a mock response." in r for r in responses)

@pytest.mark.asyncio
async def test_generate_rag_response_with_key(mock_llm_service):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.text = "This is a mock RAG answer."
    
    async def mock_generate_content(*args, **kwargs):
        return mock_response
        
    mock_llm_service.client.aio.models.generate_content = mock_generate_content

    # We mock knowledge service as well
    with patch("services.llm_service.knowledge_service.retrieve_context") as mock_retrieve:
        mock_retrieve.return_value = [] # Empty chunks for simplicity
        
        rag_response = await mock_llm_service.generate_rag_response("What is HTN?")
        
        assert rag_response.answer == "This is a mock RAG answer."
        assert isinstance(rag_response.sources, list)

@pytest.mark.asyncio
async def test_llm_service_no_key():
    with patch("services.llm_service.os.getenv", return_value=None):
        with patch("services.llm_service.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = None
            service = LLMService()
            
            rag_resp = await service.generate_rag_response("test")
            assert "disabled" in rag_resp.answer
            
            chat_resp = service.generate_chat_response_stream([])
            responses = []
            async for r in chat_resp:
                responses.append(r)
@pytest.mark.asyncio
async def test_safety_guardrail_rag(mock_llm_service):
    # Setup mock response with a drug dose
    mock_response = MagicMock()
    mock_response.text = "Take Amoxicillin 500mg twice a day."
    
    async def mock_generate_content(*args, **kwargs):
        return mock_response
        
    mock_llm_service.client.aio.models.generate_content = mock_generate_content

    with patch("services.llm_service.knowledge_service.retrieve_context") as mock_retrieve:
        mock_retrieve.return_value = []
        rag_response = await mock_llm_service.generate_rag_response("dose")
        
        # The warning should be appended because "500mg" triggers the regex
        assert "500mg" in rag_response.answer
        assert "CRITICAL SAFETY WARNING" in rag_response.answer
        assert "National Formulary of India" in rag_response.answer

@pytest.mark.asyncio
async def test_safety_guardrail_chat_stream(mock_llm_service):
    # Setup mock stream with a drug dose
    mock_chunk = MagicMock()
    mock_chunk.text = "The recommended dose is 10 mL syrup."
    
    async def mock_generate_content_stream(*args, **kwargs):
        yield mock_chunk

    mock_llm_service.client.aio.models.generate_content_stream = mock_generate_content_stream
    mock_llm_service.client.aio.models.count_tokens = AsyncMock(return_value=MagicMock(total_tokens=10))

    messages = [ChatMessage(role="user", content="dose")]
    response_stream = mock_llm_service.generate_chat_response_stream(messages)
    
    responses = []
    async for r in response_stream:
        responses.append(r)

    # 1 for context, 1 for the text chunk, 1 for the appended warning chunk
    assert any("CRITICAL SAFETY WARNING" in r for r in responses)
