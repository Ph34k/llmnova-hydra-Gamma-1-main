"""Sequential task planning system for the Gamma Engine.

This module provides a linear (non-hierarchical) planning system where
goals are broken down into sequential steps that can be tracked and
executed one at a time.

Key Components:
    - PlanStep: Individual step in a sequential plan
    - Planner: Creates and manages sequential execution plans
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class PlanStep(BaseModel):
    """Represents a single step in a sequential execution plan.
    
    Each step has a unique identifier, description, status tracking,
    and can store execution results.
    
    Attributes:
        id: Unique numeric identifier for the step (1-indexed).
        description: Human-readable description of what needs to be done.
        status: Current execution status. Valid values:
            - 'pending': Not yet started
            - 'in_progress': Currently executing
            - 'completed': Successfully finished
            - 'failed': Execution failed
        result: Optional result or error message from step execution.
    
    Examples:
        >>> step = PlanStep(
        ...     id=1,
        ...     description="Install dependencies"
        ... )
        >>> step.status = "completed"
        >>> step.result = "Successfully installed 10 packages"
    """
    id: int
    description: str
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[str] = None


class Planner:
    """Sequential task planner with LLM-powered plan generation.
    
    Creates and manages linear execution plans where steps are executed
    sequentially. Uses LLM to generate plans from high-level goals.
    
    Attributes:
        llm: LLM provider instance for plan generation.
        plan: Current list of plan steps.
    
    Examples:
        >>> from gamma_engine.core.llm import LLMProvider
        >>> llm = LLMProvider(model="gpt-4o")
        >>> planner = Planner(llm)
        >>> plan = planner.create_plan("Deploy application")
        >>> for step in plan:
        ...     print(f"{step.id}. {step.description}")
        1. Build Docker image
        2. Push to registry
        3. Deploy to Kubernetes
    """
    def __init__(self, llm_provider):
        """Initialize the Planner with an LLM provider.
        
        Args:
            llm_provider: LLM provider instance for plan generation.
        """
        self.llm = llm_provider
        self.plan: List[PlanStep] = []

    def create_plan(self, goal: str) -> List[PlanStep]:
        """Create a sequential execution plan for the given goal.
        
        Uses the LLM to generate a step-by-step plan. Attempts to parse
        JSON output from the LLM and falls back to treating the goal as
        a single step if parsing fails.
        
        Args:
            goal: High-level objective to create a plan for.
        
        Returns:
            List of PlanStep objects representing the sequential plan.
        
        Examples:
            >>> planner = Planner(llm)
            >>> plan = planner.create_plan("Set up CI/CD pipeline")
            >>> for step in plan:
            ...     print(f"{step.id}. {step.description}")
            1. Create GitHub workflow file
            2. Configure build steps
            3. Add deployment stage
        
        Notes:
            The LLM is prompted to return JSON format. If the response
            contains markdown code blocks, they are automatically stripped.
        """
        prompt = f"""
        You are an expert planner.
        Goal: {goal}

        Create a numbered list of steps to achieve this goal.
        Each step should be clear and actionable.
        Return ONLY a JSON list of strings, e.g., ["step 1", "step 2"].
        """
        messages = [
            {"role": "system", "content": "You are a precise planner."},
            {"role": "user", "content": prompt}
        ]

        response = self.llm.chat(messages)
        content = response.content

        try:
            import json

            # Basic cleanup if Markdown code blocks are used
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            steps_text = json.loads(content.strip())

            self.plan = [
                PlanStep(id=i+1, description=step)
                for i, step in enumerate(steps_text)
            ]
        except Exception as e:
            # Fallback if JSON fails - just treat entire response as one step or split by newlines
            print(f"Planning Error: {e}. Content: {content}")
            self.plan = [PlanStep(id=1, description=goal)]

        return self.plan

    def update_step(self, step_id: int, status: str, result: str = None) -> None:
        """Update the status and result of a specific plan step.
        
        Args:
            step_id: ID of the step to update.
            status: New status ('pending', 'in_progress', 'completed', 'failed').
            result: Optional result message or error details.
        
        Examples:
            >>> planner.update_step(1, "completed", "Dependencies installed")
            >>> planner.update_step(2, "failed", "Build error: missing module")
        """
        for step in self.plan:
            if step.id == step_id:
                step.status = status
                step.result = result
                break

    def get_next_step(self) -> Optional[PlanStep]:
        """Get the next pending step in the plan.
        
        Returns:
            The first PlanStep with status 'pending', or None if all steps
            are completed or in progress.
        
        Examples:
            >>> next_step = planner.get_next_step()
            >>> if next_step:
            ...     print(f"Execute: {next_step.description}")
            ...     planner.update_step(next_step.id, "in_progress")
        """
        for step in self.plan:
            if step.status == "pending":
                return step
        return None
