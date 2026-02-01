import os
import json
import asyncio
import uuid
import io
import shutil
import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from gamma_engine.core.agent import Agent
from gamma_engine.core.llm import LLMProvider
from gamma_engine.core.memory import EpisodicMemory
from gamma_engine.core.reporting import generate_report_pdf
from gamma_engine.core.logger import logger
from gamma_engine.tools.filesystem import ListFilesTool, ReadFileTool, WriteFileTool, DiffFilesTool
from gamma_engine.tools.terminal import RunBashTool
from gamma_engine.tools.web_dev import WebDevelopmentTool
from gamma_engine.tools.web_search_tool import WebSearchTool
from gamma_engine.core.scheduler import TaskScheduler
from gamma_engine.tools import get_tool_schemas

load_dotenv()

app = FastAPI(title="Gamma Engine API", version="1.5.0")

FILE_STORAGE_PATH = "file_storage"

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()
scheduler = TaskScheduler()
llm_provider = LLMProvider(model=os.getenv("LLM_MODEL", "gpt-4o"))

@app.on_event("startup")
async def startup_event():
    scheduler.start()
    os.makedirs(FILE_STORAGE_PATH, exist_ok=True)
    if not os.getenv("GAMMA_API_KEY"):
        logger.warning("GAMMA_API_KEY is not set. Server is running in an insecure mode.")
    if not os.getenv("GOOGLE_API_KEY") or not os.getenv("GOOGLE_CSE_ID"):
        logger.warning("Google Search API keys are not set. WebSearchTool will be disabled.")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.stop()

class FileChangeHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if event.is_directory:
            return
        try:
             loop = asyncio.get_event_loop()
             if loop.is_running():
                 asyncio.run_coroutine_threadsafe(
                     manager.broadcast({"type": "file_update", "action": "refresh", "path": event.src_path}),
                     loop
                 )
        except Exception as e:
            logger.error(f"File watcher error: {e}")

@app.get("/")
async def api_documentation():
    """Returns a summary of available API endpoints."""
    return JSONResponse({
        "api_version": app.version,
        "project_name": app.title,
        "endpoints": [
            {"path": "/", "method": "GET", "description": "API documentation summary."},
            {"path": "/docs", "method": "GET", "description": "Swagger UI for detailed API docs."},
            {"path": "/redoc", "method": "GET", "description": "ReDoc for alternative API docs."},
            {"path": "/ws/chat", "method": "WEBSOCKET", "description": "Main endpoint for agent interaction."},
            {"path": "/api/files/upload/{session_id}", "method": "POST", "description": "Upload a file to a session."},
            {"path": "/api/report/{session_id}/pdf", "method": "GET", "description": "Download a PDF report of a session."} 
        ]
    })

class FileWriteRequest(BaseModel):
    path: str
    content: str

def get_recursive_file_list(base_path: str, relative_path: str = ""):
    items = []
    full_path = os.path.join(base_path, relative_path)

    if not os.path.exists(full_path):
        return []

    for entry in os.scandir(full_path):
        item = {
            "name": entry.name,
            "path": os.path.join(relative_path, entry.name),
            "type": "directory" if entry.is_dir() else "file"
        }
        if entry.is_dir():
            item["children"] = get_recursive_file_list(base_path, os.path.join(relative_path, entry.name))
        items.append(item)

    # Sort: directories first, then files
    items.sort(key=lambda x: (x["type"] != "directory", x["name"]))
    return items

@app.post("/api/files/upload/{session_id}")
async def upload_file(session_id: str, file: UploadFile = File(...)):
    session_dir = os.path.join(FILE_STORAGE_PATH, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    file_path = os.path.join(session_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Broadcast file update
        await manager.broadcast({"type": "file_update", "action": "refresh"})

        logger.info(f"[{session_id}] File uploaded: {file.filename}")
        return {"filename": file.filename, "content_type": file.content_type, "size": file.size}
    except Exception as e:
        logger.error(f"[{session_id}] File upload failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Could not upload file: {e}")

@app.get("/api/files/list/{session_id}")
async def list_files_endpoint(session_id: str):
    session_dir = os.path.join(FILE_STORAGE_PATH, session_id)
    if not os.path.exists(session_dir):
        # Return empty list if session dir doesn't exist yet
        return []

    files = get_recursive_file_list(session_dir)
    return files

@app.get("/api/files/read/{session_id}")
async def read_file_endpoint(session_id: str, path: str):
    session_dir = os.path.join(FILE_STORAGE_PATH, session_id)
    file_path = os.path.join(session_dir, path)

    # Security check to prevent directory traversal
    if not os.path.abspath(file_path).startswith(os.path.abspath(session_dir)):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(file_path) or not os.path.isfile(file_path):
         raise HTTPException(status_code=404, detail="File not found")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files/write/{session_id}")
async def write_file_endpoint(session_id: str, request: FileWriteRequest):
    session_dir = os.path.join(FILE_STORAGE_PATH, session_id)
    file_path = os.path.join(session_dir, request.path)

    # Security check
    if not os.path.abspath(file_path).startswith(os.path.abspath(session_dir)):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(request.content)

        # Broadcast file update
        await manager.broadcast({"type": "file_update", "action": "refresh"})

        return {"status": "success", "path": request.path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/report/{session_id}/pdf")
async def get_report_pdf(session_id: str):
    logger.info(f"PDF report requested for session_id: {session_id}")
    memory = EpisodicMemory(session_id=session_id)
    try:
        messages = memory.get_messages()
        final_answer = "Nenhum resultado final encontrado para esta sessão."
        for msg in reversed(messages):
            if msg.get('role') == 'assistant' and 'tool_calls' not in msg:
                final_answer = msg.get('content', final_answer)
                break
        
        report_data = {"session_id": session_id, "content": final_answer}
    except Exception as e:
        logger.error(f"Failed to retrieve memory for PDF report on session {session_id}: {e}")
        report_data = {"session_id": session_id, "content": "Não foi possível recuperar os dados da sessão."}

    pdf_bytes = generate_report_pdf(report_data)
    logger.info(f"Successfully generated PDF for session_id: {session_id}")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=relatorio_{session_id}.pdf"}
    )

# --- NEW ENDPOINTS FOR FRONTEND DASHBOARD ---

@app.get("/api/scheduler/jobs")
async def get_scheduled_jobs():
    """List all scheduled jobs."""
    return scheduler.list_jobs()

@app.post("/api/scheduler/pause/{job_id}")
async def pause_job(job_id: str):
    """Pause a specific job (Implementation pending in Scheduler class, mocking for now)."""
    # Real implementation would call scheduler.pause_job(job_id)
    return {"status": "paused", "job_id": job_id}

@app.post("/api/scheduler/resume/{job_id}")
async def resume_job(job_id: str):
    """Resume a specific job."""
    return {"status": "resumed", "job_id": job_id}

@app.delete("/api/scheduler/delete/{job_id}")
async def delete_job(job_id: str):
    """Delete a specific job."""
    success = scheduler.remove_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": "deleted", "job_id": job_id}

@app.get("/api/webdev/servers")
async def get_active_servers():
    """List all active servers managed by WebDevelopmentTool."""
    # Placeholder: Ideally, tools track this globally or we scan for processes
    return [
        {"port": 3000, "pid": 1234, "status": "running", "command": "npm start"},
        {"port": 8000, "pid": 5678, "status": "running", "command": "uvicorn gamma_server:app"}
    ]

@app.post("/api/webdev/stop/{port}")
async def stop_server(port: int):
    """Stop a server on a specific port."""
    # Logic to find the process and kill it would go here.
    return {"status": "stopped", "port": port}

@app.get("/api/system/status")
async def get_system_status():
    """Get current system metrics (CPU, Memory)."""
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "active_threads": 10  # Placeholder
    }

@app.get("/api/sessions")
async def list_sessions():
    """List all available sessions from file storage."""
    sessions = []
    if os.path.exists(FILE_STORAGE_PATH):
        for entry in os.scandir(FILE_STORAGE_PATH):
            if entry.is_dir():
                 try:
                    sessions.append({
                        "id": entry.name,
                        "created_at": os.path.getctime(entry.path),
                        "files_count": len(os.listdir(entry.path))
                    })
                 except OSError:
                     pass
    return sorted(sessions, key=lambda x: x['created_at'], reverse=True)

@app.get("/api/tools")
async def list_available_tools():
    """List all available tools and their schemas."""
    return get_tool_schemas()

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    expected_key = os.getenv("GAMMA_API_KEY")
    if expected_key and token != expected_key:
        logger.warning(f"Failed auth attempt with token: {token}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication token")
        return

    await manager.connect(websocket)
    session_id = str(uuid.uuid4())
    logger.info(f"New client connected. Session ID: {session_id}")

    session_dir = os.path.join(FILE_STORAGE_PATH, session_id)
    os.makedirs(session_dir, exist_ok=True)

    tools = [
        ListFilesTool(base_path=session_dir),
        ReadFileTool(base_path=session_dir),
        WriteFileTool(base_path=session_dir),
        DiffFilesTool(base_path=session_dir),
        RunBashTool(),
        WebDevelopmentTool(),
        WebSearchTool()
    ]
    
    agent = Agent(llm_provider=llm_provider, tools=tools, session_id=session_id)
    agent.memory.load_from_file()

    await websocket.send_json({"type": "session_info", "sessionId": session_id})

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                logger.error("Invalid JSON received from client.")
                await websocket.send_json({"type": "error", "content": "Invalid JSON"})
                continue

            user_input = payload.get("message")
            if not user_input:
                continue

            logger.info(f"[{session_id}] User input: {user_input[:100]}...")
            await websocket.send_json({"type": "status", "content": "thinking"})
            agent.add_message("user", user_input)

            await websocket.send_json({"type": "thought", "content": "Creating plan..."})
            loop = asyncio.get_running_loop()
            plan = await loop.run_in_executor(None, agent.planner.create_plan, user_input)
            plan_str = "\n".join([f"{step.id}. {step.description}" for step in plan])
            agent.add_message("system", f"The plan to achieve the goal is:\n{plan_str}")
            await websocket.send_json({"type": "plan", "content": plan_str})
            logger.info(f"[{session_id}] Plan created: {plan_str}")

            response_message = await loop.run_in_executor(None, lambda: agent.llm.chat(agent.memory, agent.tool_schemas))
            agent.memory.append(response_message.model_dump())

            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    func_name = tool_call.function.name
                    args_str = tool_call.function.arguments
                    logger.info(f"[{session_id}] Executing tool: {func_name} with args {args_str}")
                    await websocket.send_json({"type": "tool_call", "tool": func_name, "args": args_str})
                    try:
                        args = json.loads(args_str)
                        result = await loop.run_in_executor(None, lambda: agent.tools[func_name].run(**args))
                    except Exception as e:
                        result = f"Error executing tool: {str(e)}"
                        logger.error(f"[{session_id}] Tool execution error for {func_name}: {e}")
                    await websocket.send_json({"type": "tool_result", "tool": func_name, "result": str(result)})
                    agent.memory.append({"role": "tool", "tool_call_id": tool_call.id, "content": str(result)})
                    if "file" in func_name:
                         await websocket.send_json({"type": "file_update", "action": "refresh"})

                    if "web_development" in func_name:
                        try:
                            if "port" in args and args.get("action") == "start":
                                port = args["port"]
                                await websocket.send_json({"type": "preview_update", "url": f"http://localhost:{port}"})
                        except Exception:
                            pass

                final_response = agent.llm.chat(agent.memory)
                agent.memory.append(final_response.model_dump())
                logger.info(f"[{session_id}] Final response generated after tool calls.")
                await websocket.send_json({"type": "final-answer", "content": final_response.content})
            else:
                logger.info(f"[{session_id}] Direct final response generated.")
                await websocket.send_json({"type": "final-answer", "content": response_message.content})

            await websocket.send_json({"type": "status", "content": "ready"})
            agent.memory.save_to_file()

    except WebSocketDisconnect:
        logger.info(f"Client disconnected. Session ID: {session_id}")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"An unexpected error occurred in websocket_endpoint for session {session_id}: {e}", exc_info=True)
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("gamma_server:app", host="0.0.0.0", port=8000, reload=True)
