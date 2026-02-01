import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel


class JobDefinition(BaseModel):
    id: str
    func_name: str
    trigger_type: str  # "date", "interval", "cron"
    trigger_args: Dict[str, Any]
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}

class ScheduleManager:
    """
    Manages background task scheduling using APScheduler.
    Allows the agent to schedule tasks to run at specific times or intervals.
    Includes persistence to JSON file.
    """
    def __init__(self, persistence_file: str = "scheduler_jobs.json"):
        self.scheduler = AsyncIOScheduler()
        self.persistence_file = persistence_file
        self.logger = logging.getLogger("gamma.scheduler")
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self._load_jobs()

    def start(self):
        """Starts the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info("Schedule Manager started.")

    def stop(self):
        """Stops the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("Schedule Manager stopped.")

    def _save_jobs(self):
        """Saves jobs to persistence file."""
        try:
            with open(self.persistence_file, 'w') as f:
                json.dump(self.jobs, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving jobs: {e}")

    def _load_jobs(self):
        """Loads jobs from persistence file."""
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, 'r') as f:
                    self.jobs = json.load(f)
                # Note: Re-scheduling loaded jobs would require mapping func_name to actual callables.
                # In this implementation, we just keep the state for reporting. 
                # Real task execution usually involves a task registry.
            except Exception as e:
                self.logger.error(f"Error loading jobs: {e}")

    def add_job(self, func, trigger_type: str, trigger_args: Dict[str, Any], job_id: str = None, args=None, kwargs=None):
        """
        Adds a job to the scheduler and saves to persistence.
        """
        if trigger_type == "date":
            trigger = DateTrigger(**trigger_args)
        elif trigger_type == "interval":
            trigger = IntervalTrigger(**trigger_args)
        elif trigger_type == "cron":
            trigger = CronTrigger(**trigger_args)
        else:
            raise ValueError(f"Unknown trigger type: {trigger_type}")

        job = self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            args=args,
            kwargs=kwargs,
            replace_existing=True
        )
        
        self.jobs[job.id] = {
            "id": job.id,
            "trigger_type": trigger_type,
            "trigger_args": trigger_args,
            "func_name": func.__name__ if hasattr(func, "__name__") else str(func),
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }
        self._save_jobs()
        
        self.logger.info(f"Job {job.id} added. Next run: {job.next_run_time}")
        return job.id

    def remove_job(self, job_id: str):
        """Removes a job by ID and updates persistence."""
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]
                self._save_jobs()
            self.logger.info(f"Job {job_id} removed.")
            return True
        except Exception as e:
            self.logger.error(f"Error removing job {job_id}: {e}")
            return False

    def list_jobs(self):
        """Lists all scheduled jobs from both APScheduler and persistent state."""
        active_jobs = {job.id: job for job in self.scheduler.get_jobs()}
        
        results = []
        for job_id, info in self.jobs.items():
            job_data = info.copy()
            if job_id in active_jobs:
                job_data["next_run_time"] = str(active_jobs[job_id].next_run_time)
                job_data["is_active"] = True
            else:
                job_data["is_active"] = False
            results.append(job_data)
        
        return results

    def get_job(self, job_id: str):
        """Gets details of a specific job."""
        if job_id in self.jobs:
            job_data = self.jobs[job_id].copy()
            active_job = self.scheduler.get_job(job_id)
            if active_job:
                job_data["next_run_time"] = str(active_job.next_run_time)
                job_data["is_active"] = True
            return job_data
        return None

# Alias for compatibility
TaskScheduler = ScheduleManager
