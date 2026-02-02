
import pytest
import json
from unittest.mock import MagicMock
from gamma_engine.core.llm import LLMProvider
from gamma_engine.interfaces.llm_provider import Message

@pytest.fixture
def mock_openai(mocker):
    return mocker.patch("gamma_engine.core.llm.OpenAI")

@pytest.fixture
def mock_redis(mocker):
    return mocker.patch("gamma_engine.core.llm.get_redis_client")

def test_chat_openai_success(mock_openai, mock_redis):
    # Setup mocks
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_redis.return_value = None # Disable cache for this test

    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(role="assistant", content="Hello!"))]
    mock_client.chat.completions.create.return_value = mock_completion

    provider = LLMProvider(model="gpt-4o")
    response = provider.chat([{"role": "user", "content": "Hi"}])

    assert response.content == "Hello!"
    assert response.role == "assistant"
    mock_client.chat.completions.create.assert_called_once()

def test_chat_cache_hit(mock_openai, mock_redis):
    # Setup cache hit
    mock_redis_client = MagicMock()
    mock_redis.return_value = mock_redis_client

    cached_msg = Message(role="assistant", content="Cached Response")
    mock_redis_client.get.return_value = cached_msg.model_dump_json()

    provider = LLMProvider(model="gpt-4o")
    response = provider.chat([{"role": "user", "content": "Hi"}])

    assert response.content == "Cached Response"
    mock_openai.return_value.chat.completions.create.assert_not_called()

def test_critique_lgtm(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="LGTM"))]
    mock_client.chat.completions.create.return_value = mock_completion

    provider = LLMProvider()
    result = provider.critique("print('hello')", "Say hello")

    assert result == "LGTM"

def test_anthropic_call(mocker, mock_redis):
    mock_anthropic = mocker.patch("gamma_engine.core.llm.anthropic.Anthropic")
    mocker.patch("os.getenv", return_value="fake_key")
    mock_redis.return_value = None

    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client

    # Mock Anthropic response structure
    mock_response = MagicMock()
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = "Claude response"
    mock_response.content = [mock_block]
    mock_client.messages.create.return_value = mock_response

    provider = LLMProvider(model="claude-3-opus")
    response = provider.chat([{"role": "user", "content": "Hi"}])

    assert response.content == "Claude response"
    mock_client.messages.create.assert_called_once()
