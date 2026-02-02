"""Task domain model for the Gamma Engine.

This module defines the core Task entity used throughout the Gamma Engine
for representing work units and their execution status.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from uuid import uuid4


@dataclass
class Task:
    """Represents a single task or work unit in the Gamma Engine.
    
    A Task encapsulates a description of work to be done, its current status,
    results, and optional subtasks for hierarchical task decomposition.
    
    Attributes:
        description: A human-readable description of the task.
        id: Unique identifier for the task (auto-generated UUID).
        status: Current status of the task. Must be one of: 'pending',
            'running', 'completed', 'failed'.
        result: Optional result or error message from task execution.
        subtasks: List of child tasks for hierarchical task decomposition.
    
    Examples:
        Create a simple task:
        
        >>> task = Task(description="Install dependencies")
        >>> print(task.status)
        pending
        
        Create a task with subtasks:
        
        >>> main_task = Task(
        ...     description="Build application",
        ...     subtasks=[
        ...         Task(description="Install dependencies"),
        ...         Task(description="Run tests"),
        ...     ]
        ... )
        
        Mark a task as completed:
        
        >>> task.mark_completed("Dependencies installed successfully")
        >>> print(task.status)
        completed
    """
    
    description: str
    id: str = field(default_factory=lambda: str(uuid4()))
    status: str = "pending"
    result: Optional[str] = None
    subtasks: List['Task'] = field(default_factory=list)

    def mark_completed(self, result: str) -> None:
        """Mark the task as completed with a result message.
        
        Args:
            result: A message describing the completion result or outcome.
                This will be stored in the task's result field.
        
        Examples:
            >>> task = Task(description="Process data")
            >>> task.mark_completed("Processed 1000 records")
            >>> assert task.status == "completed"
            >>> assert task.result == "Processed 1000 records"
        """
        self.status = "completed"
        self.result = result

    def mark_failed(self, error: str) -> None:
        """Mark the task as failed with an error message.
        
        Args:
            error: A message describing the failure reason or error.
                This will be stored in the task's result field.
        
        Examples:
            >>> task = Task(description="Connect to database")
            >>> task.mark_failed("Connection timeout")
            >>> assert task.status == "failed"
            >>> assert task.result == "Connection timeout"
        """
        self.status = "failed"
        self.result = error
