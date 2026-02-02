"""Short-term Memory (L2) for the Gamma Engine.

This module defines the ShortTermMemory class, which is responsible for
summarizing and compressing the WorkingMemory (L1) to retain more context
over a longer period.
"""

import logging
from typing import Any, Dict, List, Optional

from ..interfaces.llm_provider import Message

logger = logging.getLogger(__name__)

class ShortTermMemory:
    """
    Manages the agent's short-term memory (L2).
    This layer typically holds summarized or compressed information from working memory.
    """

    def __init__(self, session_id: str, max_summarized_messages: int = 10):
        """
        Initializes the ShortTermMemory.

        Args:
            session_id: A unique identifier for the conversation session.
            max_summarized_messages: Maximum number of summarized messages to keep.
        """
        self.session_id = session_id
        self.summarized_messages: List[Message] = []
        self.max_summarized_messages = max_summarized_messages
        logger.info(f"ShortTermMemory initialized for session {self.session_id}")

    def add_summary(self, summary_message: Message) -> None:
        """
        Adds a new summary message to short-term memory.
        Prunes older summaries if the limit is exceeded.
        """
        self.summarized_messages.append(summary_message)
        if len(self.summarized_messages) > self.max_summarized_messages:
            self.summarized_messages.pop(0) # Remove the oldest summary
        logger.debug(f"Summary added to short-term memory: {summary_message.content[:50]}...")

    def get_summaries(self) -> List[Dict[str, Any]]:
        """
        Retrieves the summarized messages as a list of dictionaries.
        """
        context_list = []
        for msg in self.summarized_messages:
            context_list.append(msg.model_dump(exclude_none=True))
        return context_list

    def clear(self) -> None:
        """Clears all summarized messages from short-term memory."""
        self.summarized_messages = []
        logger.info(f"ShortTermMemory cleared for session {self.session_id}.")

    def __str__(self) -> str:
        if not self.summarized_messages:
            return "No summarized messages."
        s = "Summarized Messages:\n"
        for msg in self.summarized_messages:
            s += f"- {msg.content[:70]}...\n"
        return s
