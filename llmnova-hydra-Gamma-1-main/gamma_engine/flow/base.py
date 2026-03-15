from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from ..core.agent import Agent

class BaseFlow(ABC):
    """Base class for execution flows supporting multiple agents."""

    def __init__(self, primary_agent: Agent, available_agents: Optional[Dict[str, Agent]] = None):
        self.primary_agent = primary_agent
        self.available_agents = available_agents or {}
        # Ensure primary agent is also in available agents
        if "primary" not in self.available_agents:
            self.available_agents["primary"] = primary_agent

    @abstractmethod
    async def execute(self, input_text: str) -> str:
        """Execute the flow with given input."""
        pass
