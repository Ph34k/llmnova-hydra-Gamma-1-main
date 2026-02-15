from typing import Any
from .base import Tool
from gamma_engine.core.logger import logger
from gamma_engine.core.training.base import LocalTrainer

class ModelTrainingTool(Tool):
    """
    A tool to initiate model fine-tuning or training jobs.
    Wraps the 'Trainer' interface to allow the Agent to orchestrate training.
    """
    def __init__(self, trainer: LocalTrainer):
        super().__init__(
            name="train_model",
            description=(
                "Initiates a model training or fine-tuning job. "
                "Use this tool when the user requests to train a new model or update an existing one "
                "with a dataset."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "dataset_path": {
                        "type": "string",
                        "description": "Path to the training dataset (CSV/JSONL)."
                    },
                    "model_name": {
                        "type": "string",
                        "description": "Name of the base model to fine-tune (e.g., 'llama-2', 'bert')."
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Directory to save the trained model artifacts."
                    }
                },
                "required": ["dataset_path", "model_name", "output_path"]
            }
        )
        self.trainer = trainer

    def execute(self, dataset_path: str, model_name: str, output_path: str, **kwargs: Any) -> str:
        """
        Executes the training job via the trainer.
        """
        try:
            logger.info(f"Initiating training job for {model_name} on {dataset_path} -> {output_path}")
            metrics = self.trainer.train(dataset_path, model_name, output_path)

            if metrics.get('status') == 'success':
                return (
                    f"Training job completed successfully.\n"
                    f"- Model: {model_name}\n"
                    f"- Output Path: {output_path}\n"
                    f"- Final Loss: {metrics.get('loss', 'N/A')}\n"
                    f"- Artifacts: {metrics.get('artifacts', [])}"
                )
            elif metrics.get('status') == 'mock_success':
                # For our simulated environment
                return (
                    f"Training simulation completed successfully.\n"
                    f"- Model: {model_name}\n"
                    f"- Output Path: {output_path}\n"
                    f"- Simulated Loss: {metrics.get('loss', 'N/A')}\n"
                    f"- Artifacts: {metrics.get('artifacts', [])}"
                )
            else:
                return f"Training job failed: {metrics.get('error', 'Unknown error')}"

        except Exception as e:
            logger.error(f"Error during training execution: {e}")
            return f"Error executing training job: {str(e)}"
