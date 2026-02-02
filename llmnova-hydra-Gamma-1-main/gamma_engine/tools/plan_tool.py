import json
from typing import Any, Dict, List

from .base import Tool


class PlanTool(Tool):
    """Manage simple multi-phase project plans (create/update/advance)."""

    def __init__(self) -> None:
        super().__init__(
            name="plan_tool",
            description="Create and advance multi-phase project plans.",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["update", "advance"]},
                    "goal": {"type": "string"},
                    "phases": {"type": "array"},
                    "current_phase_id": {"type": "integer"},
                    "next_phase_id": {"type": "integer"},
                },
                "required": ["action"],
            },
        )
        self._plan: Dict[str, Any] = {"goal": None, "phases": []}

    async def update(self, goal: str, phases: List[Dict[str, Any]]) -> str:
        self._plan = {"goal": goal, "phases": phases}
        return f"Plan updated: {json.dumps(self._plan)}"

    async def advance(self, current_phase_id: int, next_phase_id: int) -> str:
        for p in self._plan.get("phases", []):
            if p.get("id") == current_phase_id:
                p["completed"] = True
        return f"Advanced from {current_phase_id} to {next_phase_id}"

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Minimal runner: expects a dict matching parameters schema."""
        action = params.get("action")
        if action == "update":
            goal = params.get("goal", "")
            phases = params.get("phases", [])
            res = await self.update(goal, phases)
            return {"status": "ok", "result": res}
        if action == "advance":
            current = params.get("current_phase_id")
            next_id = params.get("next_phase_id")

            # Validate and coerce to ints
            try:
                current_int = int(current)  # type: ignore[arg-type]
                next_int = int(next_id)  # type: ignore[arg-type]
            except Exception:
                return {"status": "error", "error": "invalid phase ids"}

            res = await self.advance(current_int, next_int)
            return {"status": "ok", "result": res}
        return {"status": "error", "error": "unknown action"}
