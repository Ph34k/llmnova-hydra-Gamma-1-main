from typing import Dict, List, Literal, Optional, Any
from .base import Tool

_PLANNING_TOOL_DESCRIPTION = """
A planning tool that allows the agent to create and manage plans for solving complex tasks.
The tool provides functionality for creating plans, updating plan steps, and tracking progress.
"""

class PlanningTool(Tool):
    """
    A planning tool that allows the agent to create and manage plans for solving complex tasks.
    """

    def __init__(self):
        super().__init__(
            name="planning",
            description=_PLANNING_TOOL_DESCRIPTION,
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "description": "The command to execute. Available commands: create, update, list, get, set_active, mark_step, delete.",
                        "enum": [
                            "create",
                            "update",
                            "list",
                            "get",
                            "set_active",
                            "mark_step",
                            "delete",
                        ],
                        "type": "string",
                    },
                    "plan_id": {
                        "description": "Unique identifier for the plan. Required for create, update, set_active, and delete commands. Optional for get and mark_step (uses active plan if not specified).",
                        "type": "string",
                    },
                    "title": {
                        "description": "Title for the plan. Required for create command, optional for update command.",
                        "type": "string",
                    },
                    "steps": {
                        "description": "List of plan steps. Required for create command, optional for update command.",
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "step_index": {
                        "description": "Index of the step to update (0-based). Required for mark_step command.",
                        "type": "integer",
                    },
                    "step_status": {
                        "description": "Status to set for a step. Used with mark_step command.",
                        "enum": ["not_started", "in_progress", "completed", "blocked"],
                        "type": "string",
                    },
                    "step_notes": {
                        "description": "Additional notes for a step. Optional for mark_step command.",
                        "type": "string",
                    },
                },
                "required": ["command"],
            }
        )
        self.plans: Dict[str, Dict[str, Any]] = {}
        self._current_plan_id: Optional[str] = None

    def execute(
        self,
        command: str,
        plan_id: Optional[str] = None,
        title: Optional[str] = None,
        steps: Optional[List[str]] = None,
        step_index: Optional[int] = None,
        step_status: Optional[str] = None,
        step_notes: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Execute the planning tool with the given command and parameters.
        """
        try:
            if command == "create":
                return self._create_plan(plan_id, title, steps)
            elif command == "update":
                return self._update_plan(plan_id, title, steps)
            elif command == "list":
                return self._list_plans()
            elif command == "get":
                return self._get_plan(plan_id)
            elif command == "set_active":
                return self._set_active_plan(plan_id)
            elif command == "mark_step":
                return self._mark_step(plan_id, step_index, step_status, step_notes)
            elif command == "delete":
                return self._delete_plan(plan_id)
            else:
                return f"Error: Unrecognized command: {command}"
        except Exception as e:
            return f"Error executing planning command '{command}': {str(e)}"

    def _create_plan(
        self, plan_id: Optional[str], title: Optional[str], steps: Optional[List[str]]
    ) -> str:
        if not plan_id:
            return "Error: Parameter `plan_id` is required for command: create"

        if plan_id in self.plans:
            return f"Error: A plan with ID '{plan_id}' already exists. Use 'update' to modify existing plans."

        if not title:
            return "Error: Parameter `title` is required for command: create"

        if not steps or not isinstance(steps, list):
            return "Error: Parameter `steps` must be a non-empty list of strings for command: create"

        plan = {
            "plan_id": plan_id,
            "title": title,
            "steps": steps,
            "step_statuses": ["not_started"] * len(steps),
            "step_notes": [""] * len(steps),
        }

        self.plans[plan_id] = plan
        self._current_plan_id = plan_id

        return f"Plan created successfully with ID: {plan_id}\n\n{self._format_plan(plan)}"

    def _update_plan(
        self, plan_id: Optional[str], title: Optional[str], steps: Optional[List[str]]
    ) -> str:
        if not plan_id:
            return "Error: Parameter `plan_id` is required for command: update"

        if plan_id not in self.plans:
            return f"Error: No plan found with ID: {plan_id}"

        plan = self.plans[plan_id]

        if title:
            plan["title"] = title

        if steps:
            old_steps = plan["steps"]
            old_statuses = plan["step_statuses"]
            old_notes = plan["step_notes"]

            new_statuses = []
            new_notes = []

            for i, step in enumerate(steps):
                if i < len(old_steps) and step == old_steps[i]:
                    new_statuses.append(old_statuses[i])
                    new_notes.append(old_notes[i])
                else:
                    new_statuses.append("not_started")
                    new_notes.append("")

            plan["steps"] = steps
            plan["step_statuses"] = new_statuses
            plan["step_notes"] = new_notes

        return f"Plan updated successfully: {plan_id}\n\n{self._format_plan(plan)}"

    def _list_plans(self) -> str:
        if not self.plans:
            return "No plans available. Create a plan with the 'create' command."

        output = "Available plans:\n"
        for plan_id, plan in self.plans.items():
            current_marker = " (active)" if plan_id == self._current_plan_id else ""
            completed = sum(1 for status in plan["step_statuses"] if status == "completed")
            total = len(plan["steps"])
            output += f"• {plan_id}{current_marker}: {plan['title']} - {completed}/{total} steps completed\n"

        return output

    def _get_plan(self, plan_id: Optional[str]) -> str:
        if not plan_id:
            if not self._current_plan_id:
                return "Error: No active plan. Please specify a plan_id or set an active plan."
            plan_id = self._current_plan_id

        if plan_id not in self.plans:
            return f"Error: No plan found with ID: {plan_id}"

        return self._format_plan(self.plans[plan_id])

    def _set_active_plan(self, plan_id: Optional[str]) -> str:
        if not plan_id:
            return "Error: Parameter `plan_id` is required for command: set_active"

        if plan_id not in self.plans:
            return f"Error: No plan found with ID: {plan_id}"

        self._current_plan_id = plan_id
        return f"Plan '{plan_id}' is now the active plan.\n\n{self._format_plan(self.plans[plan_id])}"

    def _mark_step(
        self,
        plan_id: Optional[str],
        step_index: Optional[int],
        step_status: Optional[str],
        step_notes: Optional[str],
    ) -> str:
        if not plan_id:
            if not self._current_plan_id:
                return "Error: No active plan. Please specify a plan_id."
            plan_id = self._current_plan_id

        if plan_id not in self.plans:
            return f"Error: No plan found with ID: {plan_id}"

        if step_index is None:
            return "Error: Parameter `step_index` is required for command: mark_step"

        plan = self.plans[plan_id]

        if step_index < 0 or step_index >= len(plan["steps"]):
            return f"Error: Invalid step_index: {step_index}. Valid indices range from 0 to {len(plan['steps'])-1}."

        if step_status:
            valid_statuses = ["not_started", "in_progress", "completed", "blocked"]
            if step_status not in valid_statuses:
                return f"Error: Invalid step_status: {step_status}. Valid statuses: {', '.join(valid_statuses)}"
            plan["step_statuses"][step_index] = step_status

        if step_notes:
            plan["step_notes"][step_index] = step_notes

        return f"Step {step_index} updated in plan '{plan_id}'.\n\n{self._format_plan(plan)}"

    def _delete_plan(self, plan_id: Optional[str]) -> str:
        if not plan_id:
            return "Error: Parameter `plan_id` is required for command: delete"

        if plan_id not in self.plans:
            return f"Error: No plan found with ID: {plan_id}"

        del self.plans[plan_id]
        if self._current_plan_id == plan_id:
            self._current_plan_id = None

        return f"Plan '{plan_id}' has been deleted."

    def _format_plan(self, plan: Dict[str, Any]) -> str:
        output = f"Plan: {plan['title']} (ID: {plan['plan_id']})\n"
        output += "=" * len(output) + "\n\n"

        total = len(plan["steps"])
        completed = sum(1 for status in plan["step_statuses"] if status == "completed")
        progress = (completed / total) * 100 if total > 0 else 0

        output += f"Progress: {completed}/{total} steps completed ({progress:.1f}%)\n"
        output += "Steps:\n"

        for i, (step, status, notes) in enumerate(
            zip(plan["steps"], plan["step_statuses"], plan["step_notes"])
        ):
            status_symbol = {
                "not_started": "[ ]",
                "in_progress": "[→]",
                "completed": "[✓]",
                "blocked": "[!]",
            }.get(status, "[ ]")

            output += f"{i}. {status_symbol} {step}\n"
            if notes:
                output += f"   Notes: {notes}\n"

        return output
