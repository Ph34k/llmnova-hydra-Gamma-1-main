import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

from ..interfaces.llm_provider import Message, LLMProviderInterface
from .redis_client import get_redis_client
from .long_term_memory import LongTermMemory

logger = logging.getLogger(__name__)

class EpisodicMemory:
    """
    Manages the agent's immediate conversation history (L1 Memory).
    Supports persistence via Redis and local file storage.
    Enhanced with Semantic Summarization and Entity Extraction.
    """

    def __init__(self, session_id: str, llm_provider: Optional[LLMProviderInterface] = None, max_tokens: int = 4000, storage_path: str = "file_storage"):
        """
        Initializes the EpisodicMemory system.
        """
        if not session_id:
            raise ValueError("session_id cannot be empty.")

        self.session_id = session_id
        self.llm = llm_provider
        self.redis_key = f"session:{self.session_id}:history"
        self.redis_client = get_redis_client()
        self.messages: List[Message] = []
        self.max_tokens = max_tokens
        self.storage_path = storage_path
        self.file_path = os.path.join(storage_path, session_id, "memory.json")
        self.long_term_memory = LongTermMemory(session_id)

        self.load_from_redis()
        if not self.messages:
             self.load_from_file()

    # ... [Load/Save methods remain similar, omitted for brevity but preserved in real file] ...
    def load_from_redis(self) -> None:
        if not self.redis_client: return
        try:
            message_jsons = self.redis_client.lrange(self.redis_key, 0, -1)
            if message_jsons:
                self.messages = [Message.model_validate_json(msg_json) for msg_json in message_jsons]
        except Exception as e:
            logger.error(f"Error loading memory from Redis: {e}")

    def load_from_file(self) -> None:
        if not os.path.exists(self.file_path): return
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.messages = [Message(**msg_data) for msg_data in data]
        except Exception as e:
            logger.error(f"Error loading memory from file: {e}")

    def save_to_file(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            data = [msg.model_dump(exclude_none=True) for msg in self.messages]
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving memory to file: {e}")

    def add(self, role: str, content: str, tool_calls: Optional[List[Any]] = None) -> None:
        message = Message(role=role, content=content, tool_calls=tool_calls)
        self.append(message)

    def append(self, message: Union[Message, Dict[str, Any]]) -> None:
        if isinstance(message, dict):
            message = Message(**message)
        self.messages.append(message)
        if self.redis_client:
            self.redis_client.rpush(self.redis_key, message.model_dump_json())
        
        # Check for pruning/summarization
        if self.get_token_count() > self.max_tokens:
            self.semantic_pruning()

    def get_messages(self) -> List[Dict[str, Any]]:
        return [msg.model_dump(exclude_none=True) for msg in self.messages]

    def get_token_count(self) -> int:
        return sum(len(msg.content.split()) for msg in self.messages if msg.content)

    def semantic_pruning(self) -> None:
        """
        Intelligently summarizes older messages using LLM instead of simple deletion.
        Also extracts entities to LongTermMemory.
        """
        if len(self.messages) < 10: return

        # 1. Extract Entities from the oldest chunk
        old_chunk = self.messages[:5]
        chunk_text = "\n".join([f"{m.role}: {m.content}" for m in old_chunk])

        if self.llm:
            try:
                # Entity Extraction
                entity_prompt = f"Extract key entities (User Name, Project, Goal) from this conversation:\n{chunk_text}"
                entities = self.llm.chat([{"role": "user", "content": entity_prompt}]).content
                self.long_term_memory.add_knowledge(entities, source="conversation_history")

                # Summarization
                summary_prompt = f"Summarize this conversation concisely:\n{chunk_text}"
                summary = self.llm.chat([{"role": "user", "content": summary_prompt}]).content

                summary_msg = Message(role="system", content=f"Previous Context: {summary}")

                # Replace old messages with summary
                self.messages = [summary_msg] + self.messages[5:]
                logger.info("Memory summarized and entities extracted.")

            except Exception as e:
                logger.error(f"Semantic pruning failed: {e}")
                # Fallback to simple pruning
                self.messages = self.messages[5:]
        else:
            self.messages = self.messages[5:]

    def clear(self) -> None:
        self.messages = []
        if self.redis_client: self.redis_client.delete(self.redis_key)
        if os.path.exists(self.file_path): os.remove(self.file_path)

# Aliases
WorkingMemory = EpisodicMemory
Memory = EpisodicMemory
