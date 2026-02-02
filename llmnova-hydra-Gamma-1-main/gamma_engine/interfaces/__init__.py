"""Interfaces for the Gamma Engine.

This package contains abstract interfaces and contracts that define
the architecture of the Gamma Engine. Concrete implementations must
adhere to these interfaces.
"""

from .llm_provider import LLMProviderInterface, Message
from .tool import ToolInterface

__all__ = [
    'LLMProviderInterface',
    'Message',
    'ToolInterface',
]
