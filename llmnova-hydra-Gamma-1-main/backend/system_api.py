
import os
import psutil
from fastapi import APIRouter
from gamma_engine.core.logger import logger
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

router = APIRouter(prefix="/api/system", tags=["System"])

@router.get("/status")
def get_system_status():
    """Returns basic system metrics (CPU, Memory, Disk)."""
    try:
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "status": "online",
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "free": disk.free,
                "percent": disk.percent
            }
        }
    except Exception as e:
        logger.error(f"Error fetching system status: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/metrics")
def get_metrics():
    """Exposes Prometheus metrics for scraping."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
