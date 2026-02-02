"""Advanced cognitive core for task planning and reflection.

This module implements hierarchical task decomposition and error reflection
capabilities, allowing the agent to break down complex goals into executable
subtasks with dependency management. It also integrates advanced reasoning
strategies like Chain-of-Thought (CoT) and Tree-of-Thought (ToT),
and mechanisms for hallucination grounding.

Key Components:
    - SubTask: Individual executable task with dependencies
    - TaskTree: Hierarchical task decomposition structure
    - Brain: Cognitive core for planning and reflection
"""

import json
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from .llm import LLMProvider


class SubTask(BaseModel):
    """Represents a single executable subtask in a task decomposition.
    
    Each subtask has a unique identifier, description, status tracking,
    and can depend on other subtasks completing first.
    
    Attributes:
        id: Unique identifier for the subtask.
        description: Human-readable description of what needs to be done.
        status: Current execution status. Valid values:
            - 'pending': Not yet started
            - 'in_progress': Currently executing
            - 'completed': Successfully finished
            - 'failed': Execution failed
        dependencies: List of task IDs that must complete before this task.
    
    Examples:
        Simple task with no dependencies:
        
        >>> task = SubTask(
        ...     id="1",
        ...     description="Initialize project structure",
        ...     dependencies=[]
        ... )
        
        Task with dependencies:
        
        >>> task = SubTask(
        ...     id="3",
        ...     description="Run tests",
        ...     dependencies=["1", "2"]  # Depends on tasks 1 and 2
        ... )
    """
    id: str
    description: str
    status: str = "pending"  # pending, in_progress, completed, failed
    dependencies: List[str] = []


class TaskTree(BaseModel):
    """Represents a hierarchical task decomposition tree.
    
    Contains the original high-level goal and the list of subtasks
    needed to achieve it, with their interdependencies.
    
    Attributes:
        goal: The original high-level objective to be achieved.
        tasks: List of SubTask objects representing the decomposition.
    
    Examples:
        >>> tree = TaskTree(
        ...     goal="Build a web application",
        ...     tasks=[
        ...         SubTask(id="1", description="Setup Next.js", dependencies=[]),
        ...         SubTask(id="2", description="Create components", dependencies=["1"])
        ...     ]
        ... )
        >>> print(tree.goal)
        Build a web application
    """
    goal: str
    tasks: List[SubTask]

class Brain:
    """Advanced cognitive core for hierarchical planning and error reflection.
    
    The Brain is responsible for decomposing high-level goals into executable
    subtasks and reflecting on errors to propose fixes and replanning strategies.
    It also incorporates Chain-of-Thought (CoT) for step-by-step reasoning,
    and can be extended for Tree-of-Thought (ToT) and hallucination grounding.
    
    Attributes:
        llm: LLM provider instance for generating plans and reflections.
    
    Examples:
        Basic usage:
        
        >>> from gamma_engine.core.llm import LLMProvider
        >>> llm = LLMProvider(model="gpt-4o")
        >>> brain = Brain(llm)
        >>> tree = brain.decompose("Build a REST API")
        >>> print(len(tree.tasks))
        5
    """
    
    def __init__(self, llm: LLMProvider):
        """Initialize the Brain with an LLM provider.
        
        Args:
            llm: LLM provider instance for cognitive operations.
        """
        self.llm = llm

    def _generate_thoughts(self, prompt_messages: List[Dict[str, str]]) -> str:
        """Generates step-by-step thoughts using Chain-of-Thought (CoT)."""
        cot_prompt = [
            {"role": "system", "content": "You are an expert reasoner. Think step-by-step to arrive at the solution. Enclose your thoughts in <thought> and </thought> tags."}, 
            *prompt_messages
        ]
        response = self.llm.chat(cot_prompt)
        # Extract content between <thought> tags if present, otherwise return full content
        match = re.search(r"<thought>(.*?)</thought>", response.content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.content # Fallback if no thought tags

    def decompose(self, goal: str, tool_schemas: List[Dict[str, Any]]) -> TaskTree:
        """Decompose a high-level goal into executable subtasks with dependencies.
        
        Uses the LLM to analyze the goal and create a structured task tree
        with proper dependency ordering. The result is a TaskTree containing
        atomic, executable tasks. This method can be extended for Tree-of-Thought
        by generating multiple decompositions and evaluating them.
        
        Args:
            goal: High-level objective to be decomposed (e.g., "Build a web app").
            tool_schemas: List of available tool schemas for grounding.
        
        Returns:
            TaskTree containing the goal and list of subtasks with dependencies.
        
        Examples:
            >>> brain = Brain(llm)
            >>> tree = brain.decompose("Create a Python package", [])
            >>> for task in tree.tasks:
            ...     print(f"{task.id}: {task.description}")
            1: Initialize project structure
            2: Write setup.py
            3: Add tests
        
        Notes:
            In production, this should enforce JSON schema output from the LLM
            and include robust parsing with fallbacks.
        """
        # Placeholder for Tree-of-Thought:
        # In a full ToT implementation, we would generate multiple possible decompositions,
        # simulate their outcomes (e.g., by calling a mock executor or another LLM),
        # and then select the best one based on a scoring mechanism.
        
        # For now, we use CoT to generate a single, well-reasoned decomposition.
        prompt_messages = [
            {"role": "system", "content": f"""You are the Senior Architect of Gamma.
Break down the user's goal into atomic, executable software engineering tasks.
Consider the available tools: {tool_schemas}. Ensure tasks are actionable with these tools.
Return a JSON object with a list of tasks, each having an ID, description, and dependencies.
Example:
{{
  "goal": "Build a React App",
  "tasks": [
    {{"id": "1", "description": "Initialize Next.js project", "dependencies": []}},
    {{"id": "2", "description": "Create Navbar component", "dependencies": ["1"]}}
  ]
}}"""},
            {"role": "user", "content": f"Goal: {goal}"}
        ]
        
        # Use Chain-of-Thought for better decomposition
        thoughts = self._generate_thoughts(prompt_messages)
        
        # The actual decomposition response will be generated after the thoughts
        decomposition_prompt = prompt_messages + [
            {"role": "assistant", "content": f"<thought>{thoughts}</thought>"}
        ]
        response = self.llm.chat(decomposition_prompt)
        
        # In a real implementation, we would force JSON output mode and parse it
        # For now, we'll mock a simple parsing or assume direct JSON output
        try:
            # Attempt to parse the LLM's response as JSON
            # This is a simplification; robust parsing would be needed
            json_content = response.content.strip()
            if json_content.startswith("```json"):
                json_content = json_content[7:]
                if json_content.endswith("```"):
                    json_content = json_content[:-3]
            
            data = json.loads(json_content)
            tasks = [SubTask(**t) for t in data.get("tasks", [])]
            return tasks  # Change return type to Any
        except json.JSONDecodeError:
            # Fallback if LLM doesn't return perfect JSON
            # In a real system, this would trigger reflection or re-prompting
            print(f"Warning: LLM did not return valid JSON for decomposition. Raw response: {response.content}")
            # Create a dummy TaskTree for now
            return TaskTree(goal=goal, tasks=[SubTask(id="1", description=f"Failed to decompose: {goal}", dependencies=[])])


    def reflect_on_error(self, error: str, context: List[Dict[str, Any]]) -> str:
        """Analyze an error and propose corrective actions.
        
        Uses the LLM to perform root cause analysis on failures and suggest
        specific fixes or plan adjustments, incorporating Chain-of-Thought.
        
        Args:
            error: Error message or exception details.
            context: Conversation history and execution context for analysis.
        
        Returns:
            String containing the proposed fix or corrective action.
        
        Examples:
            >>> error = "ModuleNotFoundError: No module named 'requests'"
            >>> context = [{"role": "user", "content": "Install dependencies"}]
            >>> fix = brain.reflect_on_error(error, context)
            >>> print(fix)
            Install the 'requests' package using: pip install requests
        
        Notes:
            The quality of reflection depends heavily on the context provided.
            Include relevant execution history, code snippets, and environment info.
        """
        prompt_messages = context + [
            {"role": "system", "content": f"CRITICAL FAILURE DETECTED:\n{error}\n\nAnalyze the root cause. Propose a specific fix."} 
        ]
        
        # Use Chain-of-Thought for better reflection
        thoughts = self._generate_thoughts(prompt_messages)
        
        reflection_prompt = prompt_messages + [
            {"role": "assistant", "content": f"<thought>{thoughts}</thought>\nBased on the above thoughts, what is the specific fix?"}
        ]
        response = self.llm.chat(reflection_prompt)
        return response.content

    def _ground_tool_call(self, tool_call: Dict[str, Any], tool_schemas: List[Dict[str, Any]]) -> bool:
        """
        Performs hallucination grounding by verifying tool existence and parameters.
        This is a placeholder for a more robust implementation.
        """
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})

        # Check if tool exists
        if not any(schema.get("function", {}).get("name") == tool_name for schema in tool_schemas):
            print(f"Grounding failed: Tool '{tool_name}' does not exist.")
            return False
        
        # In a real system, you would validate args against the tool's schema
        # For now, a basic check
        if not isinstance(tool_args, dict):
            print(f"Grounding failed: Tool arguments for '{tool_name}' are not a dictionary.")
            return False

        print(f"Grounding successful for tool call: {tool_name}")
        return True

