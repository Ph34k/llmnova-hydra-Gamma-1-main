
"""Minimal, clean Agent implementation for import/type-check stability.

This file provides a small, well-typed Agent class that other modules can
import safely while the full implementation is worked on. It supports
calling tools which may be implemented synchronously or asynchronously.
"""

from typing import Any, Callable, Dict, List, Optional
import inspect
import uuid

from ..interfaces.tool import ToolInterface
from .memory import EpisodicMemory
from .planner import Planner
# Using LLM Message format for internal memory, not messaging.Message
from ..interfaces.llm_provider import Message


class Agent:
    """Lightweight Agent used as a stable placeholder.

    The goal is to provide the minimal surface other modules expect:
    - construction with a list of tools
    - an async ``run`` method that returns a string
    - a small helper to execute a tool by name supporting sync/async tools
    """

    def __init__(
        self,
        tools: List[ToolInterface],
        llm_provider: Optional[Any] = None,
        session_id: Optional[str] = None,
        event_callback: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.session_id = session_id or str(uuid.uuid4())
        self.tools: Dict[str, ToolInterface] = {t.name: t for t in tools}
        self.event_callback = event_callback
        self.llm = llm_provider
        self.memory = EpisodicMemory(session_id=self.session_id)
        self.planner = Planner(llm_provider=self.llm)

    @property
    def tool_schemas(self) -> List[Dict[str, Any]]:
        """Return the schemas of the tools."""
        return [t.schema for t in self.tools.values()]

    def add_message(self, role: str, content: str):
        """Add a message to the agent's memory."""
        message = Message(role=role, content=content, tool_calls=None)
        self.memory.append(message.model_dump())

    async def execute_tool(self, name: str, **kwargs: Any) -> Optional[str]:
        """Execute a named tool. Supports sync and async tool implementations.

        Returns the tool output as string when possible, or None if the tool is
        not found.
        """
        tool = self.tools.get(name)
        if tool is None:
            return None

        result = tool.run(**kwargs)
        if inspect.isawaitable(result):
            result = await result

        # Normalize to str when possible
        if result is None:
            return None
        return str(result)

    async def run(self, user_input: str) -> str:
        """Simple async run entry point used by callers in the codebase.

        This implementation intentionally keeps behavior trivial: it
        acknowledges the input and returns it. The method exists so that
        imports and awaitable usage of Agent.run remain correct.
        """
        # This is a placeholder. The actual run loop is in gamma_server.py
        if self.event_callback:
            await self.event_callback("assistant_message", {"content": f"Agent received: {user_input}"})
        return f"Agent received: {user_input}"
