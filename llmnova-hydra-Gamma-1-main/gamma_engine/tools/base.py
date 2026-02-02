"""Base tool implementation for the Gamma Engine.

This module provides the concrete base class that most tools should inherit from,
implementing the ToolInterface with common functionality.
"""

from typing import Any, Dict
import asyncio

from ..interfaces.tool import ToolInterface


class Tool(ToolInterface):
    """Concrete base class for Gamma Engine tools.
    
    This class provides a standard implementation of the ToolInterface,
    handling schema generation and basic initialization. Most tools should
    inherit from this class rather than directly from ToolInterface.
    
    Attributes:
        name: Unique identifier for the tool.
        description: Human-readable description of the tool's functionality.
        parameters: JSON Schema describing the tool's parameters.
    
    Examples:
        Creating a custom tool:
        
        >>> class CalculatorTool(Tool):
        ...     def __init__(self):
        ...         super().__init__(
        ...             name="calculator",
        ...             description="Performs basic math operations",
        ...             parameters={
        ...                 "type": "object",
        ...                 "properties": {
        ...                     "operation": {
        ...                         "type": "string",
        ...                         "enum": ["add", "subtract", "multiply", "divide"]
        ...                     },
        ...                     "a": {"type": "number"},
        ...                     "b": {"type": "number"}
        ...                 },
        ...                 "required": ["operation", "a", "b"]
        ...             }
        ...         )
        ...     
        ...     def execute(self, operation: str, a: float, b: float) -> float:
        ...         operations = {
        ...             "add": lambda x, y: x + y,
        ...             "subtract": lambda x, y: x - y,
        ...             "multiply": lambda x, y: x * y,
        ...             "divide": lambda x, y: x / y,
        ...         }
        ...         return operations[operation](a, b)
    """
    
    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        """Initialize the tool with its metadata.
        
        Args:
            name: Unique identifier for the tool (e.g., 'read_file').
            description: Description of what the tool does.
            parameters: JSON Schema for the tool's parameters.
        """
        self.name = name
        self.description = description
        self.parameters = parameters

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the tool's functionality.
        
        Subclasses must override this method to implement their specific logic.
        
        Args:
            **kwargs: Tool-specific parameters matching the schema.
        
        Returns:
            Tool execution result.
        
        Raises:
            NotImplementedError: If subclass doesn't implement this method.
        """
        raise NotImplementedError("Subclasses must implement execute()")

    async def run(self, *args: Any, **kwargs: Any) -> Any:
        """Async-compatible runner that calls execute().

        If a subclass implements an async execute (returns a coroutine), this
        will await it. Otherwise it will run the synchronous execute and
        return the result.
        """
        result = self.execute(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result

    def to_schema(self) -> Dict[str, Any]:
        """Generate the LLM function calling schema for this tool.
        
        Returns:
            Dictionary containing the tool schema in OpenAI function calling
            format.
        
        Examples:
            >>> tool = CalculatorTool()
            >>> schema = tool.to_schema()
            >>> print(schema['type'])
            function
            >>> print(schema['function']['name'])
            calculator
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
