"""Memory Manager for the Gamma Engine.

This module defines the MemoryManager class, which orchestrates different
memory layers (Working, Short-term, Long-term, and Episodic) to provide
a comprehensive and context-aware memory system for the agent.
"""

import logging
from typing import Any, Dict, List, Optional

from ..interfaces.llm_provider import Message
from .working_memory import WorkingMemory # Renamed from memory.py
from .episodic_memory import EpisodicStore, Episode, Action # New episodic memory components
from .short_term_memory import ShortTermMemory # New short-term memory component
from .long_term_memory import LongTermMemory # New long-term memory component

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Orchestrates different memory layers for the agent.
    
    Attributes:
        working_memory: The agent's immediate, short-term conversation history (L1).
        short_term_memory: Summarized or compressed information from working memory (L2).
        long_term_memory: Stores structured knowledge and uses RAG for retrieval (L3).
        episodic_store: Stores past experiences and reflections.
    """

    def __init__(self, session_id: str, max_working_memory_tokens: int = 4000):
        """
        Initializes the MemoryManager with different memory layers.

        Args:
            session_id: A unique identifier for the conversation session.
            max_working_memory_tokens: Max tokens for the immediate working memory.
        """
        self.session_id = session_id
        self.working_memory = WorkingMemory(session_id=session_id, max_tokens=max_working_memory_tokens)
        self.short_term_memory = ShortTermMemory(session_id=session_id)
        self.long_term_memory = LongTermMemory(session_id=session_id)
        self.episodic_store = EpisodicStore()

    def add_message(self, role: str, content: str, tool_calls: Optional[List[Any]] = None) -> None:
        """
        Adds a new message to the working memory.
        """
        self.working_memory.add(role, content, tool_calls)
        logger.debug(f"Message added to working memory: {role}: {content[:50]}...")
        # In a real system, this would also trigger summarization for short-term memory
        # and potential knowledge extraction for long-term memory.

    def get_context_for_llm(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieves the current context for the LLM, integrating information from all memory layers.
        """
        context = []
        
        # 1. Add relevant long-term memory (RAG) - Placeholder
        # In a real system, this would involve a query to long_term_memory based on current goal/beliefs
        # For now, we'll just add a generic placeholder if any knowledge exists
        if self.long_term_memory.knowledge_base:
            context.append({"role": "system", "content": "Relevant knowledge from long-term memory is available."})
            # Example: context.extend(self.long_term_memory.retrieve_knowledge(query="current goal"))

        # 2. Add short-term memory (summaries)
        context.extend(self.short_term_memory.get_summaries())

        # 3. Add working memory (recent conversation)
        context.extend(self.working_memory.get_context(limit))
        
        return context

    def record_episode(self, goal: str, context: Dict[str, Any], actions: List[Action], outcome: str, reflection: Optional[str] = None) -> None:
        """
        Records a completed experience as an episode in the episodic store.
        """
        episode = Episode(goal=goal, context=context, actions=actions, outcome=outcome, reflection=reflection)
        self.episodic_store.save_episode(episode)
        logger.info(f"Episode recorded for goal '{goal}' with outcome '{outcome}'.")
        # Also, extract knowledge from the episode for long-term memory
        self.long_term_memory.add_knowledge(content=f"Agent completed goal '{goal}' with outcome '{outcome}'. Reflection: {reflection}", source="episodic_memory")

    def get_similar_episodes(self, current_goal: str, n_results: int = 1) -> List[Episode]:
        """
        Retrieves similar past episodes from the episodic store.
        """
        return self.episodic_store.find_similar_episodes(current_goal, n_results)

    def clear_all_memory(self) -> None:
        """Clears all memory layers."""
        self.working_memory.clear()
        self.short_term_memory.clear()
        self.long_term_memory.clear()
        self.episodic_store.episodes = [] # Clear in-memory episodes
        logger.info(f"All memory cleared for session {self.session_id}.")

    def __str__(self) -> str:
        s = f"Memory Manager for session: {self.session_id}\n"
        s += f"--- Working Memory ---\n{self.working_memory}\n"
        s += f"--- Short-Term Memory ---\n{self.short_term_memory}\n"
        s += f"--- Long-Term Memory ---\n{self.long_term_memory}\n"
        s += f"--- Episodic Memory ---\n{self.episodic_store}\n"
        return s
