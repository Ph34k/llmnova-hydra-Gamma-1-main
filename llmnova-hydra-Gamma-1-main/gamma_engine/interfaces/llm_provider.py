"""LLM provider interfaces for the Gamma Engine.

This module defines the abstract interface for Large Language Model providers
and the Message data structure for LLM communication.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Represents a single message in an LLM conversation.
    
    This is the standard message format used across all LLM providers
    in the Gamma Engine, providing a unified interface regardless of
    the underlying LLM API (OpenAI, Anthropic, etc.).
    
    Attributes:
        role: The role of the message sender. Typically 'system', 'user',
            'assistant', or 'tool'.
        content: The text content of the message. May be None for messages
            that only contain tool calls.
        tool_calls: Optional list of tool/function calls requested by the
            assistant. Structure depends on the LLM provider.
    
    Examples:
        User message:
        
        >>> msg = Message(role="user", content="Hello!")
        >>> print(msg.role)
        user
        
        Assistant message with tool call:
        
        >>> msg = Message(
        ...     role="assistant",
        ...     content="I'll read that file for you",
        ...     tool_calls=[{
        ...         "id": "call_123",
        ...         "function": {"name": "read_file", "arguments": "{}"}
        ...     }]
        ... )
    """
    
    role: str = Field(..., description="Role of the message sender")
    content: Optional[str] = Field(None, description="Text content of the message")
    tool_calls: Optional[List[Any]] = Field(
        None,
        description="List of tool calls requested by the assistant"
    )


class LLMProviderInterface(ABC):
    """Abstract interface for Large Language Model providers.
    
    This interface defines the contract that all LLM providers must implement,
    allowing the Gamma Engine to work with different LLM APIs (OpenAI,
    Anthropic, Google, etc.) through a unified interface.
    
    Implementations should handle:
    - API authentication and configuration
    - Message formatting for the specific provider
    - Tool/function calling support
    - Error handling and retries
    - Rate limiting
    
    Examples:
        Implementing a custom LLM provider:
        
        >>> class MyLLMProvider(LLMProviderInterface):
        ...     def chat(self, history, tools=None):
        ...         # Call your LLM API
        ...         response = my_llm_api.complete(history)
        ...         return Message(
        ...             role="assistant",
        ...             content=response.text
        ...         )
    """
    
    @abstractmethod
    def chat(
        self,
        history: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None
    ) -> Message:
        """Send chat history to the LLM and get a response.
        
        Args:
            history: List of message dictionaries representing the conversation
                history. Each dict should have 'role' and 'content' keys at minimum.
            tools: Optional list of tool schemas for function calling. If provided,
                the LLM may choose to call tools instead of responding with text.
        
        Returns:
            A Message object containing the LLM's response, which may include
            text content and/or tool calls.
        
        Raises:
            NotImplementedError: If the subclass doesn't implement this method.
            RuntimeError: If the LLM API call fails.
        
        Examples:
            >>> provider = MyLLMProvider()
            >>> history = [{"role": "user", "content": "Hello!"}]
            >>> response = provider.chat(history)
            >>> print(response.content)
            Hello! How can I help you today?
        """
        pass

