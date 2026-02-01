import json
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..interfaces.llm_provider import Message
from .redis_client import get_redis_client

logger = logging.getLogger(__name__)

class WorkingMemory:
    """
    Manages the agent's immediate conversation history (L1 Memory) using Redis for persistence.
    """
    def __init__(self, session_id: str, max_tokens: int = 4000):
        if not session_id:
            raise ValueError("session_id cannot be empty.")
        self.session_id = session_id
        self.redis_key = f"session:{self.session_id}:history"
        self.redis_client = get_redis_client()
        self.messages: List[Message] = []
        self.max_tokens = max_tokens
        self.load_from_redis()

    def load_from_redis(self) -> None:
        if not self.redis_client:
            return
        try:
            message_jsons = self.redis_client.lrange(self.redis_key, 0, -1)
            self.messages = [Message.model_validate_json(msg_json) for msg_json in message_jsons]
        except Exception as e:
            logger.error(f"Error loading memory from Redis: {e}")
            self.messages = []

    def append(self, message: Message | Dict[str, Any]) -> None:
        if isinstance(message, dict):
            # Handle dictionary input for compatibility
            try:
                # Basic conversion, adjust fields as necessary based on Message definition
                message = Message(
                    role=message.get("role", "user"),
                    content=message.get("content", ""),
                    tool_calls=message.get("tool_calls"),
                    tool_call_id=message.get("tool_call_id")
                )
            except Exception as e:
                logger.error(f"Failed to convert dict to Message: {e}")
                return

        self.messages.append(message)
        if self.redis_client:
            try:
                self.redis_client.rpush(self.redis_key, message.model_dump_json())
            except Exception as e:
                logger.error(f"Error saving to Redis: {e}")

    def get_context(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        history = self.messages[-limit:] if limit else self.messages
        return [msg.model_dump(exclude_none=True) for msg in history]

    def save_to_file(self):
        # Local JSON backup
        try:
            os.makedirs("file_storage", exist_ok=True)
            path = f"file_storage/{self.session_id}_memory.json"
            with open(path, "w") as f:
                json.dump([m.model_dump() for m in self.messages], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory to file: {e}")

    def load_from_file(self):
        try:
            path = f"file_storage/{self.session_id}_memory.json"
            if os.path.exists(path):
                with open(path, "r") as f:
                    data = json.load(f)
                    self.messages = [Message(**m) for m in data]
        except Exception as e:
            logger.error(f"Error loading memory from file: {e}")

# Re-export WorkingMemory as EpisodicMemory for compatibility with gamma_server.py
# In a real scenario, EpisodicMemory would be a distinct class inheriting or wrapping this.
class EpisodicMemory(WorkingMemory):
    """
    Wrapper alias for WorkingMemory to satisfy gamma_server imports.
    Real EpisodicMemory (LongTerm) logic would go here.
    """
    def get_messages(self) -> List[Dict[str, Any]]:
        return [msg.model_dump() for msg in self.messages]

# Re-export as Memory for other imports
Memory = WorkingMemory
