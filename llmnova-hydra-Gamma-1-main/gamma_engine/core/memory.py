import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

from ..interfaces.llm_provider import Message
from .redis_client import get_redis_client

logger = logging.getLogger(__name__)

class EpisodicMemory:
    """
    Manages the agent's immediate conversation history (L1 Memory).
    Supports persistence via Redis and local file storage.
    """

    def __init__(self, session_id: str, max_tokens: int = 4000, storage_path: str = "file_storage"):
        """
        Initializes the EpisodicMemory system for a specific session.

        Args:
            session_id: A unique identifier for the conversation session.
            max_tokens: The maximum number of tokens this working memory should hold.
            storage_path: Base path for file storage.
        """
        if not session_id:
            raise ValueError("session_id cannot be empty.")

        self.session_id = session_id
        self.redis_key = f"session:{self.session_id}:history"
        self.redis_client = get_redis_client()
        self.messages: List[Message] = []
        self.max_tokens = max_tokens
        self.storage_path = storage_path
        self.file_path = os.path.join(storage_path, session_id, "memory.json")

        # Try to load from Redis first (fast path), but we also support file load explicitly
        self.load_from_redis()
        # Fallback to file if redis is empty or unavailable?
        if not self.messages:
             self.load_from_file()

    def load_from_redis(self) -> None:
        """Loads conversation history from Redis."""
        if not self.redis_client:
            # logger.warning("Redis client not available. Memory will be in-memory only for this session (until save_to_file is called).")
            return

        try:
            message_jsons = self.redis_client.lrange(self.redis_key, 0, -1)
            if message_jsons:
                self.messages = [Message.model_validate_json(msg_json) for msg_json in message_jsons]
                logger.info(f"Loaded {len(self.messages)} messages from Redis for session {self.session_id}")
        except Exception as e:
            logger.error(f"Error loading memory from Redis for session {self.session_id}: {e}")
            self.messages = []

    def load_from_file(self) -> None:
        """Loads conversation history from a local JSON file."""
        if not os.path.exists(self.file_path):
            # logger.info(f"No memory file found at {self.file_path}. Starting fresh.")
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.messages = []
                for msg_data in data:
                    try:
                        self.messages.append(Message(**msg_data))
                    except Exception as e:
                        logger.warning(f"Skipping invalid message in file: {e}")
            logger.info(f"Loaded {len(self.messages)} messages from file for session {self.session_id}")
        except Exception as e:
            logger.error(f"Error loading memory from file {self.file_path}: {e}")

    def save_to_file(self) -> None:
        """Saves conversation history to a local JSON file."""
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            # Convert Message objects to dicts
            data = [msg.model_dump(exclude_none=True) for msg in self.messages]
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved memory to {self.file_path}")
        except Exception as e:
            logger.error(f"Error saving memory to file {self.file_path}: {e}")

    def add(self, role: str, content: str, tool_calls: Optional[List[Any]] = None) -> None:
        """
        Adds a new message to the memory and persists it.
        """
        message = Message(role=role, content=content, tool_calls=tool_calls)
        self.append(message)

    def append(self, message: Union[Message, Dict[str, Any]]) -> None:
        """
        Appends a Message object or dict to memory and persists it to Redis.
        """
        if isinstance(message, dict):
            try:
                message = Message(**message)
            except Exception as e:
                logger.error(f"Failed to convert dict to Message: {e}")
                return

        self.messages.append(message)

        # Persist to Redis
        if self.redis_client:
            try:
                serialized_message = message.model_dump_json()
                self.redis_client.rpush(self.redis_key, serialized_message)
            except Exception as e:
                logger.error(f"Error saving message to Redis for session {self.session_id}: {e}")
        
        self.prune()

    def get_messages(self) -> List[Dict[str, Any]]:
        """
        Retrieves the conversation messages as a list of dictionaries.
        """
        return [msg.model_dump(exclude_none=True) for msg in self.messages]

    def get_context(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieves the conversation context as a list of dictionaries.
        """
        history = self.messages[-limit:] if limit else self.messages
        
        context_list = []
        for msg in history:
            context_list.append(msg.model_dump(exclude_none=True))
        return context_list

    def get_token_count(self) -> int:
        """
        Estimates the current token count of the messages in memory.
        """
        total_words = sum(len(msg.content.split()) for msg in self.messages if msg.content)
        return total_words

    def summarize(self) -> Optional[Message]:
        """
        Summarizes older messages to reduce context size.
        """
        if len(self.messages) > 10:
            old_messages = self.messages[:-5]
            summary_content = f"Summary of {len(old_messages)} previous messages..."
            summary_message = Message(role="system", content=summary_content)
            self.messages = [summary_message] + self.messages[-5:]
            logger.info(f"Memory summarized. New message count: {len(self.messages)}")
            return summary_message
        return None

    def prune(self) -> None:
        """
        Prunes messages from memory if the token count exceeds max_tokens.
        """
        while self.get_token_count() > self.max_tokens and len(self.messages) > 1:
            removed_message = self.messages.pop(0)
            logger.info(f"Pruned message from Memory: {removed_message.content[:50]}...")
            if self.redis_client:
                try:
                    self.redis_client.lpop(self.redis_key)
                except Exception as e:
                    logger.error(f"Error pruning message from Redis: {e}")

        if self.get_token_count() > self.max_tokens:
            self.summarize()

    def clear(self) -> None:
        """Clears all messages from memory and from Redis."""
        self.messages = []
        if self.redis_client:
            try:
                self.redis_client.delete(self.redis_key)
                logger.info(f"Cleared memory for session {self.session_id} from Redis.")
            except Exception as e:
                logger.error(f"Error clearing memory from Redis for session {self.session_id}: {e}")

        if os.path.exists(self.file_path):
             try:
                os.remove(self.file_path)
             except Exception as e:
                 logger.error(f"Error deleting memory file: {e}")

# Aliases
WorkingMemory = EpisodicMemory
Memory = EpisodicMemory
