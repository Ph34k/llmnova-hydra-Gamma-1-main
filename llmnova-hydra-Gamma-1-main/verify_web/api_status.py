from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

@app.get("/status")
async def get_status():
    """
    Auto-generated endpoint for /status
    """
    return {"message": "Welcome to the /status endpoint!", "method": "GET"}
