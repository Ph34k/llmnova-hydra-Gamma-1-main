"""Episodic Memory implementation for the Gamma Engine.

This module defines the data structures and store for managing the agent's
episodic memory, which records past experiences, actions, and reflections.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4
import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class Action:
    """Represents a single action taken by the agent within an episode."""
    tool_name: str
    arguments: Dict[str, Any]
    result_summary: Optional[str] = None

@dataclass
class Episode:
    """Represents a single episode of the agent's experience."""
    id: str = field(default_factory=lambda: str(uuid4()))
    goal: str
    context: Dict[str, Any] # Initial state and objective
    actions: List[Action] = field(default_factory=list)
    outcome: str # e.g., "success", "failure"
    reflection: Optional[str] = None # Why it worked or failed
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class EpisodicStore:
    """Manages the storage and retrieval of agent episodes."""
    episodes: List[Episode] = field(default_factory=list)
    # In a real system, this would be backed by a persistent store (e.g., database, vector DB)

    def save_episode(self, episode: Episode) -> None:
        """Saves a new episode to the store."""
        self.episodes.append(episode)
        logger.info(f"Episode saved: {episode.id} for goal '{episode.goal}' with outcome '{episode.outcome}'")

    def find_similar_episodes(self, current_goal: str, n_results: int = 1) -> List[Episode]:
        """
        Finds and returns similar past episodes based on the current goal.
        This is a placeholder for a more sophisticated similarity search (e.g., using embeddings).
        """
        logger.info(f"Searching for similar episodes for goal: '{current_goal}'")
        # For demonstration, return the most recent successful episode if any
        successful_episodes = [e for e in self.episodes if e.outcome == "success"]
        if successful_episodes:
            # Sort by timestamp descending
            successful_episodes.sort(key=lambda x: x.timestamp, reverse=True)
            return successful_episodes[:n_results]
        return []

    def __str__(self) -> str:
        if not self.episodes:
            return "No episodes recorded."
        s = "Episodic Memory:\n"
        for episode in self.episodes:
            s += f"- ID: {episode.id}\n"
            s += f"  Goal: {episode.goal}\n"
            s += f"  Outcome: {episode.outcome}\n"
            s += f"  Timestamp: {episode.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            if episode.reflection:
                s += f"  Reflection: {episode.reflection[:100]}...\n"
            s += f"  Actions: {len(episode.actions)} actions\n"
        return s
