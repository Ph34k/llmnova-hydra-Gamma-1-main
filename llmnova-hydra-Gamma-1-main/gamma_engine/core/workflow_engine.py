
from typing import Dict, List, Any, Callable
from gamma_engine.core.scheduler import TaskScheduler
from gamma_engine.core.logger import logger

class WorkflowEngine:
    def __init__(self, scheduler: TaskScheduler):
        self.scheduler = scheduler
        self.workflows: Dict[str, List[Callable]] = {}

    def register_workflow(self, name: str, steps: List[Callable]):
        """
        Registers a sequence of steps as a workflow.
        """
        self.workflows[name] = steps
        logger.info(f"Registered workflow: {name}")

    def execute_workflow(self, name: str, context: Dict[str, Any]):
        """
        Executes the registered workflow, passing context between steps.
        This is a simplistic sequential execution.
        """
        if name not in self.workflows:
            logger.error(f"Workflow '{name}' not found.")
            return

        logger.info(f"Starting workflow: {name}")
        for step in self.workflows[name]:
            try:
                # Each step takes context and returns updated context
                context = step(context)
                logger.info(f"Step '{step.__name__}' completed.")
            except Exception as e:
                logger.error(f"Workflow '{name}' failed at step '{step.__name__}': {e}")
                break

        logger.info(f"Workflow '{name}' completed.")
        return context

# Example Steps (Hydra-style)
def ingest_step(context: Dict[str, Any]) -> Dict[str, Any]:
    file_path = context.get('file_path')
    # ... logic from ingestion pipeline ...
    print(f"Ingesting {file_path}...")
    context['embedding_id'] = "123"
    return context

def train_step(context: Dict[str, Any]) -> Dict[str, Any]:
    embedding_id = context.get('embedding_id')
    # ... logic from trainer ...
    print(f"Training on data {embedding_id}...")
    context['model_id'] = "model_v1"
    return context

def deploy_step(context: Dict[str, Any]) -> Dict[str, Any]:
    model_id = context.get('model_id')
    # ... logic from deployment ...
    print(f"Deploying {model_id}...")
    context['endpoint'] = "http://api/model_v1"
    return context
