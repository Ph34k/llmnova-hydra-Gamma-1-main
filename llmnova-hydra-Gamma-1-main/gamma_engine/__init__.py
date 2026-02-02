"""Gamma Engine - Google-Grade Autonomous AI Architecture.

The Gamma Engine is an advanced autonomous AI agent framework with a clean
architecture, async-first design, and comprehensive tooling for building
intelligent autonomous systems.

Main Components:
    - domain: Core domain models and entities
    - interfaces: Abstract interfaces defining contracts
    - core: Core logic (Agent, LLM providers, Brain)
    - tools: Capabilities (filesystem, shell, browser, etc.)
    - adapters: I/O adapters (terminal, websocket)

Example:
    Basic agent usage:
    
    >>> from gamma_engine.core.agent import Agent
    >>> from gamma_engine.core.llm import LLMProvider
    >>> from gamma_engine.tools import ListFilesTool, ReadFileTool
    >>> 
    >>> llm = LLMProvider(model="gpt-4o")
    >>> tools = [ListFilesTool(), ReadFileTool()]
    >>> agent = Agent(llm_provider=llm, tools=tools)
    >>> 
    >>> import asyncio
    >>> result = asyncio.run(agent.run("List files in current directory"))
"""

__version__ = "1.0.0"
__author__ = "Gamma Engine Team"

from .domain import Task
from .interfaces import LLMProviderInterface, Message, ToolInterface

__all__ = [
    '__version__',
    'Task',
    'ToolInterface',
    'LLMProviderInterface',
    'Message',
]
