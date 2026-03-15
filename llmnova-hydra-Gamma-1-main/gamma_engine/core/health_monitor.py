
import asyncio
import psutil
from typing import Callable, Optional
from gamma_engine.core.logger import logger

class HealthMonitor:
    """
    Background service that monitors system vitals and triggers alerts or self-healing actions.
    """
    def __init__(self, interval: int = 10, cpu_threshold: float = 90.0, mem_threshold: float = 90.0):
        self.interval = interval
        self.cpu_threshold = cpu_threshold
        self.mem_threshold = mem_threshold
        self.is_running = False
        self.alert_callback: Optional[Callable[[str], None]] = None

    def start(self):
        self.is_running = True
        asyncio.create_task(self._monitor_loop())
        logger.info("Health Monitor started.")

    def stop(self):
        self.is_running = False
        logger.info("Health Monitor stopped.")

    def set_alert_callback(self, callback: Callable[[str], None]):
        self.alert_callback = callback

    async def _monitor_loop(self):
        while self.is_running:
            try:
                cpu = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory().percent

                if cpu > self.cpu_threshold:
                    self._trigger_alert(f"High CPU Usage: {cpu}%")
                    # Self-healing: Pause low-priority tasks (e.g., training) if possible
                    # TODO: Integrate with TaskScheduler/TrainingService to pause

                if mem > self.mem_threshold:
                    self._trigger_alert(f"High Memory Usage: {mem}%")

                # Log metrics for potential Loki ingestion
                logger.debug(f"System Vitals - CPU: {cpu}%, MEM: {mem}%")

            except Exception as e:
                logger.error(f"Health Monitor error: {e}")

            await asyncio.sleep(self.interval)

    def _trigger_alert(self, message: str):
        logger.warning(f"ALERT: {message}")
        if self.alert_callback:
            self.alert_callback(message)
