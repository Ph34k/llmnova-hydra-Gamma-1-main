
from typing import Dict, Any, List, Optional
from uuid import uuid4
from enum import Enum
from pydantic import BaseModel, Field
import time
import threading

class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TrainingJob(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid4()))
    model_name: str
    dataset_path: str
    output_path: str
    status: JobStatus = JobStatus.QUEUED
    metrics: Optional[Dict[str, Any]] = None
    artifacts: List[str] = []
    created_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None

class TrainingService:
    def __init__(self, trainer):
        self.trainer = trainer
        self.jobs: Dict[str, TrainingJob] = {}
        self.queue: List[str] = []
        self._worker_thread = None
        self._stop_event = threading.Event()

    def submit_job(self, dataset_path: str, model_name: str, output_path: str) -> str:
        job = TrainingJob(
            dataset_path=dataset_path,
            model_name=model_name,
            output_path=output_path
        )
        self.jobs[job.job_id] = job
        self.queue.append(job.job_id)
        print(f"Job {job.job_id} submitted.")

        # Start worker if not running
        if not self._worker_thread or not self._worker_thread.is_alive():
            self._start_worker()

        return job.job_id

    def get_job_status(self, job_id: str) -> Optional[TrainingJob]:
        return self.jobs.get(job_id)

    def _start_worker(self):
        self._worker_thread = threading.Thread(target=self._process_queue)
        self._worker_thread.daemon = True
        self._worker_thread.start()

    def _process_queue(self):
        print("Worker started processing queue...")
        while not self._stop_event.is_set():
            if not self.queue:
                time.sleep(1)
                continue

            job_id = self.queue.pop(0)
            job = self.jobs[job_id]

            try:
                print(f"Starting job {job_id}...")
                job.status = JobStatus.RUNNING

                # Execute Training via the Trainer implementation
                metrics = self.trainer.train(
                    job.dataset_path,
                    job.model_name,
                    job.output_path
                )

                job.status = JobStatus.COMPLETED
                job.metrics = metrics
                job.artifacts = metrics.get('artifacts', [])
                job.completed_at = time.time()
                print(f"Job {job_id} completed successfully.")

            except Exception as e:
                job.status = JobStatus.FAILED
                job.metrics = {"error": str(e)}
                print(f"Job {job_id} failed: {e}")

    def stop(self):
        self._stop_event.set()
        if self._worker_thread:
            self._worker_thread.join()
