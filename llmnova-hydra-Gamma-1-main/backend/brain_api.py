
from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
from pydantic import BaseModel

from gamma_engine.core.workflow_engine import WorkflowEngine
from gamma_engine.core.long_term_memory import LongTermMemory
from gamma_engine.core.logger import logger

router = APIRouter(prefix="/api/brain", tags=["Brain"])

# These will be injected from gamma_server.py
workflow_engine: WorkflowEngine = None
long_term_memory: LongTermMemory = None

class MemoryQuery(BaseModel):
    query: str
    limit: int = 5

@router.get("/workflows")
def get_active_workflows():
    """Returns the state of active workflows."""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow Engine not initialized")

    # Return minimal info for UI
    return {
        eid: {
            "name": ctx["workflow_name"],
            "status": ctx.get("status", "running"),
            "steps": [
                {"id": n, "status": attr.get("status", "pending")}
                for n, attr in ctx["graph"].nodes(data=True)
            ]
        }
        for eid, ctx in workflow_engine.active_contexts.items()
    }

@router.post("/memory/search")
def search_memory(query: MemoryQuery):
    """Searches Long Term Memory."""
    if not long_term_memory:
        raise HTTPException(status_code=503, detail="Long Term Memory not initialized")

    results = long_term_memory.retrieve_knowledge(query.query, query.limit)
    return results
