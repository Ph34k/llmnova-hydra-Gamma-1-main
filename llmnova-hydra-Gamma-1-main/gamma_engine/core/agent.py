"""
Robust Agent implementation integrating OpenManus-style autonomous execution loop.
"""

import asyncio
import json
import logging
import uuid
import traceback
from typing import Any, Callable, Dict, List, Optional

from ..interfaces.tool import ToolInterface
from .memory import EpisodicMemory
from .planner import Planner
from ..interfaces.llm_provider import Message
from .browser_helper import BrowserContextHelper

logger = logging.getLogger(__name__)

class Agent:
    """
    Autonomous Agent that executes a think-act loop to solve tasks.

    Integrates planning, memory, LLM interaction, and tool execution.
    """

    def __init__(
        self,
        tools: List[ToolInterface],
        llm_provider: Optional[Any] = None,
        session_id: Optional[str] = None,
        event_callback: Optional[Callable[..., Any]] = None,
        max_steps: int = 30
    ) -> None:
        self.session_id = session_id or str(uuid.uuid4())
        self.tools: Dict[str, ToolInterface] = {t.name: t for t in tools}
        self.event_callback = event_callback
        self.llm = llm_provider
        self.memory = EpisodicMemory(session_id=self.session_id)
        self.planner = Planner(llm_provider=self.llm)
        self.max_steps = max_steps
        self.browser_helper = BrowserContextHelper(self)
        self.system_prompt = (
            "You are Gamma, an advanced AI assistant capable of solving complex tasks. "
            "You have access to a variety of tools. Use them wisely. "
            "Break down problems into steps and execute them one by one. "
            "If you need to browse the web, use the available browser tools. "
            "Always explain your reasoning before taking actions."
        )

    @property
    def tool_schemas(self) -> List[Dict[str, Any]]:
        """Return the schemas of the tools."""
        return [t.schema for t in self.tools.values()]

    def add_message(self, role: str, content: str):
        """Add a message to the agent's memory."""
        message = Message(role=role, content=content, tool_calls=None)
        self.memory.append(message.model_dump())

    async def _emit(self, event_type: str, data: Dict[str, Any]):
        """Helper to emit events if a callback is registered."""
        if self.event_callback:
            try:
                await self.event_callback(event_type, data)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")

    async def execute_tool(self, name: str, **kwargs: Any) -> Any:
        """Execute a named tool."""
        tool = self.tools.get(name)
        if tool is None:
            return f"Error: Tool '{name}' not found."

        try:
            # Helper to run sync/async
            if asyncio.iscoroutinefunction(tool.run) or asyncio.iscoroutinefunction(tool.execute):
                 result = await tool.run(**kwargs)
            else:
                 result = tool.run(**kwargs)
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {e}\n{traceback.format_exc()}")
            return f"Error executing tool '{name}': {e}"

    async def run(self, user_input: str) -> str:
        """
        Executes the main agent loop: Plan -> Think -> Act -> Repeat.
        """
        logger.info(f"Agent {self.session_id} started run with input: {user_input}")

        # 1. Initialize Context
        self.add_message("user", user_input)
        # Ensure system prompt is present (simplified check)
        has_system = any(m.role == "system" for m in self.memory.messages)
        if not has_system:
             # Prepend system prompt (a bit hacky with current memory, but works)
             self.memory.messages.insert(0, Message(role="system", content=self.system_prompt))

        # 2. Planning Phase
        await self._emit("status", {"content": "planning"})
        try:
            plan = await asyncio.to_thread(self.planner.create_plan, user_input)
            plan_str = "\n".join([f"{step.id}. {step.description}" for step in plan])

            self.add_message("system", f"The initial plan to achieve the goal is:\n{plan_str}")
            await self._emit("plan", {"content": plan_str})
        except Exception as e:
            logger.warning(f"Planning failed: {e}. Proceeding without explicit plan.")

        # 3. Execution Loop
        await self._emit("status", {"content": "thinking"})

        step_count = 0
        final_answer = ""

        while step_count < self.max_steps:
            step_count += 1
            logger.info(f"Step {step_count}/{self.max_steps}")

            # THINK
            try:
                # Augment prompt with browser state if active
                browser_prompt = await self.browser_helper.format_next_step_prompt()

                # We temporarily inject this prompt or just rely on the memory updates done by helper
                # The helper might add a user message with image.
                # But we also want to guide the *next* step.

                # Ideally, we append a system instruction about the browser state to the history
                # without persisting it permanently if it's just transient state?
                # For now, let's treat it as a transient system message for this turn.

                context = self.memory.get_context()

                # If the helper didn't add an image but returned text (prompt), we can append it
                # to the last message or as a system message.
                if browser_prompt and "Current Browser State" in browser_prompt:
                     context.append({"role": "system", "content": browser_prompt})

                response = await asyncio.to_thread(
                    self.llm.chat,
                    history=context,
                    tools=self.tool_schemas
                )
            except Exception as e:
                logger.error(f"LLM Chat error: {e}")
                await self._emit("error", {"content": f"LLM Error: {e}"})
                break

            self.memory.append(response.model_dump())

            # If plain text response (thought or final answer)
            if response.content:
                await self._emit("thought", {"content": response.content})

            # ACT
            if response.tool_calls:
                await self._emit("status", {"content": "acting"})

                for tool_call in response.tool_calls:
                    func_name = tool_call.function.name
                    args_str = tool_call.function.arguments
                    tool_call_id = tool_call.id

                    logger.info(f"Executing tool: {func_name} with args: {args_str}")
                    await self._emit("tool_call", {"tool": func_name, "args": args_str})

                    try:
                        args = json.loads(args_str)
                        result = await self.execute_tool(func_name, **args)
                    except json.JSONDecodeError:
                        result = f"Error: Invalid JSON arguments for {func_name}"
                    except Exception as e:
                        result = f"Error: {e}"

                    result_str = str(result)
                    logger.info(f"Tool Result ({func_name}): {result_str[:100]}...")

                    # Store result in memory
                    self.memory.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": result_str,
                        "name": func_name
                    })

                    await self._emit("tool_result", {"tool": func_name, "result": result_str})

                    # Special handling for file updates to refresh UI
                    if "file" in func_name or "write" in func_name:
                         await self._emit("file_update", {"action": "refresh"})

                # After tools, loop back to THINK
                continue

            else:
                # No tools called -> Final Answer (or question to user)
                final_answer = response.content
                logger.info("Agent reached final answer/stop condition.")
                await self._emit("final-answer", {"content": final_answer})
                break

        if step_count >= self.max_steps:
             logger.warning("Agent reached maximum steps limit.")
             await self._emit("error", {"content": "Maximum steps reached without final resolution."})

        self.memory.save_to_file()
        await self._emit("status", {"content": "ready"})
        return final_answer
