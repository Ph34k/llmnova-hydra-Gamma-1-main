"""Schedule Tool for the Gamma Engine.

This module defines the ScheduleTool, which allows the agent to schedule
tasks for future or recurring execution using cron expressions or intervals.
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from uuid import uuid4
import datetime

from .base import Tool

logger = logging.getLogger(__name__)

@dataclass
class CronTask:
    """Represents a task to be scheduled using a cron expression."""
    name: str
    cron_expression: str # e.g., "0 9 * * 1-5" for 9 AM on weekdays
    prompt: str # The prompt/goal for the agent to execute
    repeat: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class IntervalTask:
    """Represents a task to be scheduled at a fixed interval."""
    name: str
    interval_seconds: int
    prompt: str # The prompt/goal for the agent to execute
    repeat: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)

class ScheduleTool(Tool):
    """
    A tool for scheduling tasks for future or recurring execution.
    """

    def __init__(self):
        super().__init__(
            name="schedule",
            description=(
                "Schedule tasks for future or recurring execution using cron expressions or intervals. "
                "Actions: 'schedule_cron', 'schedule_interval', 'cancel_task'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["schedule_cron", "schedule_interval", "cancel_task"],
                        "description": "The scheduling action to perform."
                    },
                    "name": {
                        "type": "string",
                        "description": "A unique name for the scheduled task."
                    },
                    "prompt": {
                        "type": "string",
                        "description": "The prompt or goal for the agent to execute when the task runs."
                    },
                    "cron_expression": {
                        "type": "string",
                        "description": "A cron expression (e.g., '0 9 * * 1-5' for 9 AM on weekdays) for cron tasks."
                    },
                    "interval_seconds": {
                        "type": "integer",
                        "description": "Interval in seconds for interval tasks."
                    },
                    "repeat": {
                        "type": "boolean",
                        "description": "Whether the task should repeat. Defaults to True."
                    },
                    "task_id": {
                        "type": "string",
                        "description": "The ID of the task to cancel."
                    }
                },
                "required": ["action", "name", "prompt"]
            }
        )
        self.scheduled_tasks: Dict[str, Any] = {} # Placeholder for a real scheduler

    def schedule_cron(self, name: str, cron_expression: str, prompt: str, repeat: bool = True) -> str:
        """
        Schedules a task using a cron expression.
        """
        task = CronTask(name=name, cron_expression=cron_expression, prompt=prompt, repeat=repeat)
        self.scheduled_tasks[task.id] = task
        logger.info(f"Cron task '{name}' scheduled with ID: {task.id}")
        return f"Cron task '{name}' scheduled with ID: {task.id}"

    def schedule_interval(self, name: str, interval_seconds: int, prompt: str, repeat: bool = True) -> str:
        """
        Schedules a task to run at a fixed interval.
        """
        task = IntervalTask(name=name, interval_seconds=interval_seconds, prompt=prompt, repeat=repeat)
        self.scheduled_tasks[task.id] = task
        logger.info(f"Interval task '{name}' scheduled with ID: {task.id}")
        return f"Interval task '{name}' scheduled with ID: {task.id}"

    def cancel_task(self, task_id: str) -> str:
        """
        Cancels a scheduled task by its ID.
        """
        if task_id in self.scheduled_tasks:
            task_name = self.scheduled_tasks[task_id].name
            del self.scheduled_tasks[task_id]
            logger.info(f"Task '{task_name}' with ID '{task_id}' cancelled.")
            return f"Task '{task_name}' with ID '{task_id}' cancelled."
        else:
            return f"Error: Task with ID '{task_id}' not found."

    def execute(self, action: str, **kwargs) -> Any:
        """
        Executes the specified scheduling action.
        """
        if action == "schedule_cron":
            return self.schedule_cron(
                name=kwargs.get("name"),
                cron_expression=kwargs.get("cron_expression"),
                prompt=kwargs.get("prompt"),
                repeat=kwargs.get("repeat", True)
            )
        elif action == "schedule_interval":
            return self.schedule_interval(
                name=kwargs.get("name"),
                interval_seconds=kwargs.get("interval_seconds"),
                prompt=kwargs.get("prompt"),
                repeat=kwargs.get("repeat", True)
            )
        elif action == "cancel_task":
            return self.cancel_task(task_id=kwargs.get("task_id"))
        else:
            return f"Error: Unknown scheduling action '{action}'"
