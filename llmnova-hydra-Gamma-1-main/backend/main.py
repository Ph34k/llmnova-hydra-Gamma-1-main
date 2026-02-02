"""
Backend API Server - Clean Architecture Entry Point
"""
import os

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse
import io

from gamma_engine.adapters.websocket_adapter import WebSocketAdapter
from gamma_engine.core.llm import LLMProvider
from gamma_engine.tools.filesystem import (ListFilesTool, ReadFileTool,
                                           WriteFileTool)
from gamma_engine.tools.terminal import RunBashTool
from gamma_engine.core.reporting import generate_report_pdf
from gamma_engine.core.memory import EpisodicMemory

load_dotenv()

# FastAPI app
app = FastAPI(title="Gamma Engine API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize dependencies
llm_provider = LLMProvider(model=os.getenv("LLM_MODEL", "gpt-4o"))
tools = [
    ListFilesTool(),
    ReadFileTool(),
    WriteFileTool(),
    RunBashTool()
]
episodic_memory = EpisodicMemory()

# Create WebSocket adapter
ws_adapter = WebSocketAdapter(llm_provider=llm_provider, tools=tools)


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for agent interactions."""
    # TODO: Add authentication
    # token = websocket.query_params.get("token")
    # if not validate_token(token):
    #     await websocket.close(code=1008)
    #     return
    
    await ws_adapter.handle_connection(websocket)


@app.get("/api/report/{session_id}/pdf")
async def get_report_pdf(session_id: str):
    """
    Generates and returns a PDF report for a given session.
    """
    # NOTE: This is a simplified implementation. In a real-world scenario,
    # you would fetch the actual final answer/report data based on the session_id.
    # Here, we are using a placeholder content.
    
    # Fetching the last message from the episodic memory for the session
    try:
        messages = episodic_memory.get_messages(session_id)
        # Find the last message from the assistant that is a final answer
        final_answer = "Nenhum resultado final encontrado para esta sessão."
        for msg in reversed(messages):
            if msg.get('sender') == 'assistant' and msg.get('type') == 'final-answer':
                final_answer = msg.get('content', final_answer)
                break
        
        report_data = {
            "session_id": session_id,
            "content": final_answer
        }
    except Exception:
        # Fallback if memory fails or session not found
        report_data = {
            "session_id": session_id,
            "content": "Não foi possível recuperar os dados da sessão. Este é um relatório de exemplo."
        }

    pdf_bytes = generate_report_pdf(report_data)
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=relatorio_{session_id}.pdf"}
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
