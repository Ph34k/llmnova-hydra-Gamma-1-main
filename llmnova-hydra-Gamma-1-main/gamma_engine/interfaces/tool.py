"""Tool interfaces for the Gamma Engine.

This module defines the abstract base class for all tools used by the agent.
Tools provide concrete capabilities like file system operations, shell commands,
web browsing, and more.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class ToolInterface(ABC):
    """Abstract base class for all Gamma Engine tools.
    
    All tools must inherit from this interface and implement the execute()
    and to_schema() methods. This ensures a consistent interface for the
    agent to interact with various capabilities.
    
    Attributes:
        name: Unique identifier for the tool (e.g., 'read_file', 'run_bash').
        description: Human-readable description of what the tool does.
            This is shown to the LLM to help it decide when to use the tool.
    
    Examples:
        Implementing a simple tool:
        
        >>> class EchoTool(ToolInterface):
        ...     def __init__(self):
        ...         self.name = "echo"
        ...         self.description = "Echoes back the input text"
        ...     
        ...     def execute(self, text: str) -> str:
        ...         return f"Echo: {text}"
        ...     
        ...     def to_schema(self...):
        ...         return {
        ...             "type": "function",
        ...             "function": {
        ...                 "name": self.name,
        ...                 "description": self.description,
        ...                 "parameters": {
        ...                     "type": "object",
        ...                     "properties": {
        ...                         "text": {"type": "string"}
        ...                     },
        ...                     "required": ["text"]
        ...                 }
        ...             }
        ...         }
    """
    
    name: str
    description: str

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the tool's primary functionality.
        
        This method contains the core logic of the tool. It receives parameters
        as keyword arguments and returns the tool's result.
        
        Args:
            **kwargs: Tool-specific parameters. The structure should match
                the schema defined in to_schema().
        
        Returns:
            The result of the tool execution. Type depends on the specific tool.
        
        Raises:
            NotImplementedError: If the subclass doesn't implement this method.
            Exception: Tool-specific exceptions based on the implementation.
        """
        pass

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Optional runner wrapper. Subclasses or the concrete Tool base
        may provide an async-compatible run() method. By default this
        forwards to execute().
        """
        return self.execute(*args, **kwargs)

    @abstractmethod
    def to_schema(self) -> Dict[str, Any]:
        """Return the JSON schema for the tool compatible with LLM function calling.
        
        The schema describes the tool's name, description, and parameters in a
        format that can be sent to LLM APIs (OpenAI, Anthropic, etc.) for
        function calling.
        
        Returns:
            A dictionary containing the tool schema in OpenAI function calling
            format, with keys 'type' and 'function'.
        
        Raises:
            NotImplementedError: If the subclass doesn't implement this method.
        
        Examples:
            >>> tool = MyTool()
            >>> schema = tool.to_schema()
            >>> print(schema['function']['name'])
            my_tool
        """
        pass
