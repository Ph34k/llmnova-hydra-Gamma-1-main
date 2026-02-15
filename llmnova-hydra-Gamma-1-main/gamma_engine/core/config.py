
import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # API & Security
    gamma_api_key: str = Field(default="", env="GAMMA_API_KEY")
    allowed_origins: str = Field(default="*", env="ALLOWED_ORIGINS")

    # LLM & RAG
    llm_model: str = Field(default="gpt-4o", env="LLM_MODEL")
    rag_provider: str = Field(default="vertex", env="RAG_PROVIDER")

    # Google Cloud
    google_cloud_project: str = Field(default="", env="GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str = Field(default="", env="GOOGLE_CLOUD_LOCATION")

    # System
    health_monitor_interval: int = 10
    cpu_alert_threshold: float = 90.0
    mem_alert_threshold: float = 90.0

    # Training
    training_output_dir: str = Field(default="models/fine-tuned", env="TRAINING_OUTPUT_DIR")

    class Config:
        env_file = ".env"

settings = Settings()
