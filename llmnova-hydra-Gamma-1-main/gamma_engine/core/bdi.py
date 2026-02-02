"""BDI (Belief-Desire-Intention) model components for the Gamma Engine.

This module defines the core data structures for an agent's beliefs, desires (goals),
and intentions (plans), forming the cognitive architecture.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

from gamma_engine.domain.task import Task # Assuming Task can represent a Goal

logger = logging.getLogger(__name__)

@dataclass
class Belief:
    """Represents a single belief or fact about the world."""
    content: str
    source: Optional[str] = None # e.g., "user_input", "tool_output", "observation"
    timestamp: Any = field(default_factory=lambda: "current_time") # Placeholder for actual timestamp

@dataclass
class BeliefSet:
    """Manages the agent's beliefs about the world."""
    beliefs: List[Belief] = field(default_factory=list)

    def add_belief(self, content: str, source: Optional[str] = None) -> None:
        """Adds a new belief to the set."""
        new_belief = Belief(content=content, source=source)
        self.beliefs.append(new_belief)
        logger.debug(f"Belief added: {new_belief}")

    def get_beliefs(self, filter_source: Optional[str] = None) -> List[Belief]:
        """Retrieves beliefs, optionally filtered by source."""
        if filter_source:
            return [b for b in self.beliefs if b.source == filter_source]
        return self.beliefs

    def update_from_observation(self, observation: str, source: str = "observation") -> None:
        """Updates beliefs based on a new observation."""
        # In a real system, this would involve more sophisticated parsing and integration
        self.add_belief(content=observation, source=source)
        logger.info(f"BeliefSet updated with observation from {source}.")

    def __str__(self) -> str:
        return "\n".join([f"- {b.content} (Source: {b.source})" for b in self.beliefs])

@dataclass
class GoalSet:
    """Manages the agent's desires or goals."""
    goals: List[Task] = field(default_factory=list) # Using Task to represent a Goal
    current_goal: Optional[Task] = None

    def add_goal(self, description: str, parent_id: Optional[str] = None) -> Task:
        """Adds a new goal to the set."""
        new_goal = Task(description=description, status="pending")
        if parent_id:
            # Find parent and add as subtask, or handle as top-level if parent not found
            found_parent = False
            for goal in self.goals:
                if goal.id == parent_id:
                    goal.subtasks.append(new_goal)
                    found_parent = True
                    break
            if not found_parent:
                logger.warning(f"Parent goal with ID {parent_id} not found. Adding new goal as top-level.")
                self.goals.append(new_goal)
        else:
            self.goals.append(new_goal)
        logger.info(f"Goal added: {new_goal.description}")
        return new_goal

    def set_current_goal(self, goal_id: str) -> Optional[Task]:
        """Sets a specific goal as the current active goal."""
        for goal in self.goals:
            if goal.id == goal_id:
                self.current_goal = goal
                logger.info(f"Current goal set to: {goal.description}")
                return goal
            # Also check subtasks
            for subtask in goal.subtasks:
                if subtask.id == goal_id:
                    self.current_goal = subtask
                    logger.info(f"Current goal set to: {subtask.description}")
                    return subtask
        logger.warning(f"Goal with ID {goal_id} not found.")
        return None

    def get_current_goal(self) -> Optional[Task]:
        """Returns the current active goal."""
        return self.current_goal

    def is_goal_satisfied(self, goal: Task) -> bool:
        """Checks if a given goal is satisfied."""
        # This is a placeholder. Real satisfaction check would be more complex.
        return goal.status == "completed"

    def __str__(self) -> str:
        s = "Goals:\n"
        for goal in self.goals:
            s += f"- {goal.description} (Status: {goal.status})\n"
            for subtask in goal.subtasks:
                s += f"  - {subtask.description} (Status: {subtask.status})\n"
        return s

@dataclass
class IntentionPool:
    """Manages the agent's current intentions or plans."""
    current_plan: List[Dict[str, Any]] = field(default_factory=list) # A list of planned actions/steps

    def set_plan(self, plan_steps: List[Dict[str, Any]]) -> None:
        """Sets the current plan."""
        self.current_plan = plan_steps
        logger.info(f"New plan set with {len(plan_steps)} steps.")

    def get_next_intention(self) -> Optional[Dict[str, Any]]:
        """Retrieves the next intention (step) from the current plan."""
        if self.current_plan:
            return self.current_plan.pop(0) # Get and remove the first step
        return None

    def is_plan_empty(self) -> bool:
        """Checks if the current plan is empty."""
        return not self.current_plan

    def __str__(self) -> str:
        if not self.current_plan:
            return "No active plan."
        s = "Current Plan:\n"
        for i, step in enumerate(self.current_plan):
            s += f"  {i+1}. {step}\n"
        return s
