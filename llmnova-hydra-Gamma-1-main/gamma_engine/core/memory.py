import json
import logging
from typing import Any, Dict, List, Optional

from ..interfaces.llm_provider import Message
from .redis_client import get_redis_client
from .episodic_memory import EpisodicMemory

logger = logging.getLogger(__name__)

class Memory:
    """
    Legacy wrapper for WorkingMemory to support older imports.
    """
    pass

class WorkingMemory:
    """
    Manages the agent's immediate conversation history (L1 Memory) using Redis for persistence.
    Each conversation is stored in a separate list in Redis, keyed by a session_id.
    """

    def __init__(self, session_id: str, max_tokens: int = 4000):
        """
        Initializes the WorkingMemory system for a specific session.

        Args:
            session_id: A unique identifier for the conversation session.
            max_tokens: The maximum number of tokens this working memory should hold.
        """
        if not session_id:
            raise ValueError("session_id cannot be empty.")

        self.session_id = session_id
        self.redis_key = f"session:{self.session_id}:history"
        self.redis_client = get_redis_client()
        self.messages: List[Message] = []
        self.max_tokens = max_tokens

        self.load_from_redis()

    def load_from_redis(self) -> None:
        """Loads conversation history from Redis."""
        if not self.redis_client:
            logger.warning("Redis client not available. Memory will be in-memory only for this session.")
            return

        try:
            message_jsons = self.redis_client.lrange(self.redis_key, 0, -1)
            self.messages = [Message.model_validate_json(msg_json) for msg_json in message_jsons]
            logger.info(f"Loaded {len(self.messages)} messages from Redis for session {self.session_id}")
        except Exception as e:
            logger.error(f"Error loading memory from Redis for session {self.session_id}: {e}")
            self.messages = []

    def add(self, role: str, content: str, tool_calls: Optional[List[Any]] = None) -> None:
        """
        Adds a new message to the memory and persists it to Redis.
        """
        message = Message(role=role, content=content, tool_calls=tool_calls)
        self.append(message)

    def append(self, message: Message) -> None:
        """
        Appends a Message object to memory and persists it to Redis.
        """
        self.messages.append(message)
        if self.redis_client:
            try:
                serialized_message = message.model_dump_json()
                self.redis_client.rpush(self.redis_key, serialized_message)
            except Exception as e:
                logger.error(f"Error saving message to Redis for session {self.session_id}: {e}")
        
        # After adding, check if memory exceeds max_tokens and prune if necessary
        self.prune()

    def get_context(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieves the conversation context as a list of dictionaries.
        """
        history = self.messages[-limit:] if limit else self.messages
        
        # The LLM provider expects a list of dicts, not Message objects.
        # We also need to filter out None values, as some providers are strict.
        context_list = []
        for msg in history:
            # model_dump() is similar to dict() but for pydantic models
            context_list.append(msg.model_dump(exclude_none=True))
        return context_list

    def get_token_count(self) -> int:
        """
        Estimates the current token count of the messages in memory.
        This is a placeholder and would require a proper tokenizer in a real implementation.
        """
        # Very basic estimation: count words
        total_words = sum(len(msg.content.split()) for msg in self.messages if msg.content)
        return total_words # Assuming 1 word ~ 1 token for simplicity

    def summarize(self) -> Optional[Message]:
        """
        Summarizes older messages to reduce context size.
        This is a placeholder for a more sophisticated summarization logic.
        """
        if len(self.messages) > 5: # Example: summarize if more than 5 messages
            old_messages = self.messages[:-5]
            # In a real implementation, an LLM would summarize old_messages
            summary_content = f"Summary of {len(old_messages)} previous messages..."
            summary_message = Message(role="system", content=summary_content)
            self.messages = [summary_message] + self.messages[-5:]
            logger.info(f"WorkingMemory summarized. New message count: {len(self.messages)}")
            return summary_message
        return None

    def prune(self) -> None:
        """
        Prunes messages from memory if the token count exceeds max_tokens.
        This is a placeholder for a more sophisticated pruning logic (e.g., importance-based).
        """
        while self.get_token_count() > self.max_tokens and len(self.messages) > 1:
            # Remove oldest message until within limits or only one message left
            removed_message = self.messages.pop(0)
            logger.info(f"Pruned message from WorkingMemory: {removed_message.content[:50]}...")
            # In a real system, this would also remove from Redis or mark for archival
            if self.redis_client:
                try:
                    # This is inefficient for large lists, better to use LTRIM
                    self.redis_client.ltrim(self.redis_key, 1, -1) 
                except Exception as e:
                    logger.error(f"Error pruning message from Redis: {e}")
        if self.get_token_count() > self.max_tokens:
            self.summarize() # Try to summarize if still too large after pruning

    def clear(self) -> None:
        """Clears all messages from memory and from Redis."""
        self.messages = []
        if self.redis_client:
            try:
                self.redis_client.delete(self.redis_key)
                logger.info(f"Cleared memory for session {self.session_id} from Redis.")
            except Exception as e:
                logger.error(f"Error clearing memory from Redis for session {self.session_id}: {e}")