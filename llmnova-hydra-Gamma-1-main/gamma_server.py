import os
import json
import asyncio
import uuid
import io
import shutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from gamma_engine.core.agent import Agent
from gamma_engine.core.llm import LLMProvider
from gamma_engine.core.memory import EpisodicMemory
from gamma_engine.core.reporting import generate_report_pdf
from gamma_engine.core.logger import logger
from gamma_engine.core.rag_service import RAGService
from gamma_engine.tools.filesystem import ListFilesTool, ReadFileTool, WriteFileTool, DiffFilesTool
from gamma_engine.tools.terminal import RunBashTool
from gamma_engine.tools.web_dev import WebDevTool
from gamma_engine.tools.web_search_tool import WebSearchTool
from gamma_engine.tools.rag_tool import KnowledgeBaseSearchTool
from gamma_engine.core.scheduler import TaskScheduler

load_dotenv()

app = FastAPI(title="Gamma Engine API", version="1.6.0")

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
rag_service = RAGService(
    project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION")
)

@app.on_event("startup")
def startup_event():
    scheduler.start()
    os.makedirs(FILE_STORAGE_PATH, exist_ok=True)
    if not os.getenv("GAMMA_API_KEY"):
        logger.warning("GAMMA_API_KEY is not set. Server is running in an insecure mode.")
    if not os.getenv("GOOGLE_API_KEY") or not os.getenv("GOOGLE_CSE_ID"):
        logger.warning("Google Search API keys are not set. WebSearchTool will be disabled.")
    if not rag_service.is_configured:
        logger.warning("Vertex AI RAG Service is not configured. RAG tools will be disabled.")

@app.on_event("shutdown")
def shutdown_event():
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
def api_documentation():
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

@app.post("/api/files/upload/{session_id}")
def upload_file(session_id: str, file: UploadFile = File(...)):
    session_dir = os.path.join(FILE_STORAGE_PATH, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    file_path = os.path.join(session_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"[{session_id}] File uploaded: {file.filename}")

        # Upload to RAG service
        if rag_service.is_configured:
            corpus_name = rag_service.create_or_get_corpus(f"session-{session_id}-corpus")
            if corpus_name:
                # In a real scenario, you'd upload the file to GCS first, then pass the GCS URI
                # For this example, we'll pass the local path and assume rag_service handles it
                # or that it's a placeholder for GCS upload.
                uploaded_rag_doc_name = rag_service.upload_document_to_corpus(corpus_name, file_path, file.filename)
                if uploaded_rag_doc_name:
                    logger.info(f"[{session_id}] File {file.filename} also uploaded to RAG corpus: {uploaded_rag_doc_name}")
                else:
                    logger.error(f"[{session_id}] Failed to upload {file.filename} to RAG corpus.")
            else:
                logger.error(f"[{session_id}] Failed to get/create RAG corpus for session.")
        else:
            logger.warning(f"[{session_id}] RAG service not configured, skipping upload to RAG corpus.")

        return {"filename": file.filename, "content_type": file.content_type, "size": file.size}
    except Exception as e:
        logger.error(f"[{session_id}] File upload failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Could not upload file: {e}")

@app.get("/api/report/{session_id}/pdf")
def get_report_pdf(session_id: str):
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
        WebDevTool(),
        WebSearchTool(),
        KnowledgeBaseSearchTool(rag_service=rag_service, corpus_display_name=f"session-{session_id}-corpus")
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
