from typing import Any
import psutil
from .base import Tool
from gamma_engine.core.logger import logger

class SystemStatusTool(Tool):
    """
    A tool to check the system's health and resource usage.
    """
    def __init__(self):
        super().__init__(
            name="check_system_status",
            description=(
                "Check the system's CPU, Memory, and Disk usage. "
                "Use this tool to monitor system health or diagnose performance issues."
            ),
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        )

    def execute(self, **kwargs: Any) -> str:
        """
        Returns the current system status.
        """
        try:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            status = (
                f"System Status:\n"
                f"- CPU Usage: {cpu}%\n"
                f"- Memory Usage: {mem.percent}% (Used: {mem.used / (1024**3):.2f} GB / Total: {mem.total / (1024**3):.2f} GB)\n"
                f"- Disk Usage: {disk.percent}% (Free: {disk.free / (1024**3):.2f} GB)"
            )
            return status
        except Exception as e:
            logger.error(f"Error checking system status: {e}")
            return f"Error checking system status: {str(e)}"
