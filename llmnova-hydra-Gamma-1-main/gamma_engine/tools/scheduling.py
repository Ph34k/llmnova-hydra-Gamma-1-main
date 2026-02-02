import logging
from typing import Any, Dict, Optional

from gamma_engine.core.scheduler import ScheduleManager
from gamma_engine.tools.base import Tool

logger = logging.getLogger("gamma.tools.scheduling")

class ScheduleTool(Tool):
    """
    Tool for scheduling tasks to run at a specific time or interval.
    Interfaces with the ScheduleManager.
    """
    def __init__(self, schedule_manager: Optional[ScheduleManager] = None):
        self.schedule_manager = schedule_manager or ScheduleManager()
        
        super().__init__(
            name="schedule_tool",
            description=(
                "Schedule tasks to run in the background. "
                "Actions: 'schedule', 'remove', 'list', 'status'. "
                "Trigger types: 'date', 'interval', 'cron'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["schedule", "remove", "list", "status"],
                        "description": "The action to perform."
                    },
                    "job_id": {
                        "type": "string",
                        "description": "Unique ID for the job (required for 'remove', 'status')."
                    },
                    "trigger_type": {
                        "type": "string",
                        "enum": ["date", "interval", "cron"],
                        "description": "Type of trigger (required for 'schedule')."
                    },
                    "trigger_args": {
                        "type": "object",
                        "description": "Arguments for the trigger (e.g., {'seconds': 60} for interval)."
                    },
                    "task_description": {
                        "type": "string",
                        "description": "Description of the task to be executed."
                    }
                },
                "required": ["action"]
            }
        )

    def execute(self, action: str, **kwargs: Any) -> Any:
        # Lazy start the scheduler
        self.schedule_manager.start()
        try:
            if action == "schedule":
                trigger_type = kwargs.get("trigger_type")
                trigger_args = kwargs.get("trigger_args")
                job_id = kwargs.get("job_id")
                description = kwargs.get("task_description")

                # Validate types
                if not isinstance(trigger_type, str) or not isinstance(trigger_args, dict):
                    return "Error: 'trigger_type' must be a string and 'trigger_args' must be a dict."

                return self._schedule_task(trigger_type, trigger_args, job_id, description)
            elif action == "remove":
                return self._remove_task(kwargs.get("job_id"))
            elif action == "list":
                return self._list_tasks()
            elif action == "status":
                return self._get_status(kwargs.get("job_id"))
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            logger.error(f"Error executing ScheduleTool: {e}")
            return f"Error: {e}"

    def _schedule_task(self, trigger_type: Optional[str], trigger_args: Optional[Dict[str, Any]], job_id: Optional[str] = None, description: Optional[str] = None) -> str:
        if not trigger_type or not trigger_args:
            return "Error: 'trigger_type' and 'trigger_args' are required for schedule action."
        
        # In a real system, we'd pass a task handler. For now, we simulate with a log function.
        def task_handler():
            logger.info(f"Executing scheduled task: {description or job_id}")
            print(f"EXECUTING TASK: {description or job_id}")

        new_job_id = self.schedule_manager.add_job(
            task_handler,
            trigger_type=trigger_type,
            trigger_args=trigger_args,
            job_id=job_id
        )
        return f"Task scheduled successfully. Job ID: {new_job_id}"

    def _remove_task(self, job_id: Optional[str]) -> str:
        if not job_id:
            return "Error: 'job_id' is required for remove action."
        success = self.schedule_manager.remove_job(job_id)
        if success:
            return f"Job {job_id} removed successfully."
        else:
            return f"Failed to remove job {job_id} (it may not exist)."

    def _list_tasks(self) -> str:
        jobs = self.schedule_manager.list_jobs()
        if not jobs:
            return "No scheduled tasks found."
        
        lines = ["Scheduled Tasks:"]
        for job in jobs:
            status = "ACTIVE" if job.get("is_active") else "INACTIVE"
            next_run = job.get("next_run_time", "N/A")
            lines.append(f"- {job['id']}: {job['trigger_type']} | Status: {status} | Next run: {next_run}")
        return "\n".join(lines)

    def _get_status(self, job_id: Optional[str]) -> str:
        if not job_id:
            return "Error: 'job_id' is required for status action."
        job = self.schedule_manager.get_job(job_id)
        if not job:
            return f"No job found with ID: {job_id}"
        return str(job)
