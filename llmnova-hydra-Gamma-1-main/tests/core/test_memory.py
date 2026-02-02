import uuid
from unittest.mock import MagicMock

import pytest

# Import the classes to be tested
from gamma_engine.core.memory import Memory
from gamma_engine.interfaces.llm_provider import Message


@pytest.fixture
def mock_redis_client(mocker):
    """Mocks the redis_client global variable to return a MagicMock instance."""
    mock_client = MagicMock()
    # Patch the global variable, not the getter function
    mocker.patch('gamma_engine.core.redis_client.redis_client', mock_client)
    return mock_client

def test_memory_load_from_redis(mock_redis_client):
    """Tests that memory is correctly loaded from Redis on initialization."""
    session_id = str(uuid.uuid4())
    redis_key = f"session:{session_id}:history"
    
    # Setup mock to return a message
    persisted_message = Message(role="user", content="I was persisted")
    mock_redis_client.lrange.return_value = [persisted_message.model_dump_json()]
    
    # Initialize Memory, which should trigger load_from_redis
    mem = Memory(session_id=session_id)
    
    # Assert that lrange was called correctly
    mock_redis_client.lrange.assert_called_once_with(redis_key, 0, -1)
    
    # Assert that the message was loaded
    assert len(mem.messages) == 1
    assert mem.messages[0].content == "I was persisted"

def test_memory_add_and_append(mock_redis_client):
    """Tests that adding/appending messages calls rpush on the redis client."""
    session_id = str(uuid.uuid4())
    redis_key = f"session:{session_id}:history"
    
    # Set lrange to return nothing so we start fresh
    mock_redis_client.lrange.return_value = []
    
    mem = Memory(session_id=session_id)
    
    # Test the add method
    mem.add(role="user", content="Hello")
    
    # Test the append method
    assistant_msg = Message(role="assistant", content="Hi there")
    mem.append(assistant_msg)
    
    assert len(mem.messages) == 2
    
    # Check that rpush was called for both messages
    assert mock_redis_client.rpush.call_count == 2
    # Check the last call to rpush
    mock_redis_client.rpush.assert_called_with(redis_key, assistant_msg.model_dump_json())

def test_memory_clear(mock_redis_client):
    """Tests that clearing memory calls delete on the redis client."""
    session_id = str(uuid.uuid4())
    redis_key = f"session:{session_id}:history"
    
    mock_redis_client.lrange.return_value = []
    mem = Memory(session_id=session_id)
    
    mem.add("user", "A message to be cleared")
    
    # Clear the memory
    mem.clear()
    
    assert len(mem.messages) == 0
    mock_redis_client.delete.assert_called_once_with(redis_key)

def test_init_requires_session_id():
    """Tests that Memory cannot be initialized without a session_id."""
    with pytest.raises(ValueError):
        Memory(session_id="")
    with pytest.raises(TypeError):
        Memory()