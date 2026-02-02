"""FastAPI WebSocket Adapter for the Agent."""
import asyncio
import json
from typing import List

from fastapi import WebSocket

from ..core.agent import Agent
from ..interfaces.llm_provider import LLMProviderInterface
from ..interfaces.tool import ToolInterface


class WebSocketAdapter:
    """Adapter for running the Agent via WebSocket connections."""

    def __init__(self, llm_provider: LLMProviderInterface, tools: List[ToolInterface]):
        self.llm_provider = llm_provider
        self.tools = tools

    async def handle_connection(self, websocket: WebSocket) -> None:
        """
        Handle a WebSocket connection.
        Each connection gets its own Agent instance with isolated memory.
        """
        await websocket.accept()

        # Create agent instance for this connection
        agent = Agent(
            llm_provider=self.llm_provider,
            tools=self.tools,
            event_callback=lambda event_type, data: asyncio.create_task(
                self._handle_event(websocket, event_type, data)
            )
        )

        try:
            while True:
                data = await websocket.receive_text()
                
                try:
                    payload = json.loads(data)
                except json.JSONDecodeError:
                    await websocket.send_json({"type": "error", "content": "Invalid JSON"})
                    continue

                user_input = payload.get("message")
                if not user_input:
                    continue

                await websocket.send_json({"type": "status", "content": "thinking"})

                # Run the agent
                result = await agent.run(user_input)

                await websocket.send_json({"type": "status", "content": "ready"})

        except Exception as e:
            await websocket.send_json({"type": "error", "content": str(e)})
            await websocket.close()

    async def _handle_event(self, websocket: WebSocket, event_type: str, data: dict) -> None:
        """Handle events from the agent and send them via WebSocket."""
        if event_type == "assistant_message":
            await websocket.send_json({"type": "message", "content": data["content"]})
        
        elif event_type == "tool_call":
            await websocket.send_json({
                "type": "tool_call",
                "tool": data["tool"],
                "args": data["args"]
            })
        
        elif event_type == "tool_result":
            await websocket.send_json({
                "type": "tool_result",
                "tool": data.get("tool"),
                "result": str(data["result"])
            })
            
            # Notify frontend to refresh file list if filesystem changed
            if data.get("tool") and "file" in data["tool"]:
                await websocket.send_json({"type": "file_update", "action": "refresh"})
