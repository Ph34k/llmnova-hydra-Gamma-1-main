
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from gamma_engine.core.logger import logger

class PlanStep(BaseModel):
    id: int
    description: str
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[str] = None
    subtasks: List['PlanStep'] = []  # Hierarchical planning

class Planner:
    """
    Enhanced Planner with Hierarchical Planning and Re-planning capabilities.
    """
    def __init__(self, llm_provider):
        self.llm = llm_provider
        self.plan: List[PlanStep] = []

    def create_plan(self, goal: str) -> List[PlanStep]:
        """
        Creates a high-level plan.
        """
        prompt = f"""
        Goal: {goal}
        Create a execution plan. Return a JSON list of strings.
        Example: ["Step 1", "Step 2"]
        """
        try:
            response = self.llm.chat([{"role": "user", "content": prompt}])
            steps_text = self._parse_json(response.content)
            self.plan = [PlanStep(id=i+1, description=s) for i, s in enumerate(steps_text)]
            return self.plan
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            return [PlanStep(id=1, description=goal)]

    def create_subtasks(self, step_id: int) -> List[PlanStep]:
        """
        Decomposes a step into subtasks (Hierarchical).
        """
        step = next((s for s in self.plan if s.id == step_id), None)
        if not step: return []

        prompt = f"""
        Parent Task: {step.description}
        Break this down into subtasks. Return JSON list of strings.
        """
        try:
            response = self.llm.chat([{"role": "user", "content": prompt}])
            sub_texts = self._parse_json(response.content)
            step.subtasks = [PlanStep(id=i+1, description=s) for i, s in enumerate(sub_texts)]
            return step.subtasks
        except Exception as e:
            logger.error(f"Subtask planning failed: {e}")
            return []

    def replan(self, failed_step_id: int, error_msg: str) -> List[PlanStep]:
        """
        Adjusts the plan after a failure.
        """
        current_plan_str = "\n".join([f"{s.id}. {s.description} ({s.status})" for s in self.plan])
        prompt = f"""
        Current Plan:
        {current_plan_str}
        
        Step {failed_step_id} failed with error: {error_msg}
        
        Generate a NEW JSON list of steps to recover and complete the goal.
        Start from the failed step.
        """
        try:
            response = self.llm.chat([{"role": "user", "content": prompt}])
            new_steps_text = self._parse_json(response.content)

            # Keep completed steps
            completed = [s for s in self.plan if s.status == "completed"]

            # Create new steps
            new_steps = [PlanStep(id=len(completed)+i+1, description=s) for i, s in enumerate(new_steps_text)]

            self.plan = completed + new_steps
            logger.info("Replanning successful.")
            return self.plan
        except Exception as e:
            logger.error(f"Replanning failed: {e}")
            return self.plan

    def _parse_json(self, content: str) -> List[str]:
        import json
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content.strip())
