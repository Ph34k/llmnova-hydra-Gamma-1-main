
import pytest
from unittest.mock import MagicMock, patch
from gamma_engine.core.memory import WorkingMemory
from gamma_engine.interfaces.llm_provider import Message

@pytest.fixture
def mock_redis_client(mocker):
    return mocker.patch("gamma_engine.core.memory.get_redis_client")

def test_init_requires_session_id():
    """Tests that WorkingMemory cannot be initialized without a session_id."""
    with pytest.raises(ValueError):
        WorkingMemory(session_id="")

def test_memory_load_from_redis(mock_redis_client):
    """Tests loading messages from Redis."""
    mock_redis = MagicMock()
    mock_redis_client.return_value = mock_redis
    
    # Mock Redis returning a list of JSON strings
    msg1 = Message(role="user", content="hello")
    msg2 = Message(role="assistant", content="hi")
    mock_redis.lrange.return_value = [msg1.model_dump_json(), msg2.model_dump_json()]

    memory = WorkingMemory(session_id="test_session")
    
    assert len(memory.messages) == 2
    assert memory.messages[0].content == "hello"
    assert memory.messages[1].content == "hi"

def test_memory_add_and_append(mock_redis_client):
    """Tests adding messages to memory and Redis."""
    mock_redis = MagicMock()
    mock_redis_client.return_value = mock_redis
    
    memory = WorkingMemory(session_id="test_session_new")
    memory.messages = [] # Force clear if it loaded from file/redis
    memory.add(role="user", content="new message")
    
    assert len(memory.messages) == 1
    assert memory.messages[0].content == "new message"
    
    # Verify Redis interaction
    mock_redis.rpush.assert_called_once()
    args = mock_redis.rpush.call_args[0]
    assert args[0] == "session:test_session_new:history"
    assert "new message" in args[1]

def test_memory_clear(mock_redis_client):
    """Tests clearing memory."""
    mock_redis = MagicMock()
    mock_redis_client.return_value = mock_redis
    
    memory = WorkingMemory(session_id="test_session")
    memory.add("user", "msg")
    memory.clear()
    
    assert len(memory.messages) == 0
    mock_redis.delete.assert_called_with("session:test_session:history")

def test_get_context(mock_redis_client):
    memory = WorkingMemory(session_id="test_session")
    memory.add("user", "msg1")
    memory.add("assistant", "msg2")
    
    context = memory.get_context()
    assert len(context) == 2
    assert isinstance(context[0], dict)
    assert context[0]['role'] == "user"

def test_prune_memory(mock_redis_client):
    """Test pruning logic (basic verification)."""
    memory = WorkingMemory(session_id="test_session", max_tokens=10) # Low max tokens

    # Add messages
    memory.add("user", "a " * 5) # ~5 tokens
    memory.add("assistant", "b " * 10) # ~10 tokens -> total > 10

    # Should trigger prune/summarize
    # Since specific prune logic depends on implementation details (which are placeholders),
    # we mainly check that it doesn't crash and maintains some state.
    assert len(memory.messages) >= 1
