from typing import Any, Dict, Optional, TYPE_CHECKING
import json
import logging
from ..interfaces.llm_provider import Message

if TYPE_CHECKING:
    from .agent import Agent

logger = logging.getLogger(__name__)

NEXT_STEP_PROMPT = """
Current Browser State:
{url_placeholder}
{tabs_placeholder}
{content_above_placeholder}
{content_below_placeholder}
{results_placeholder}

Based on user needs, proactively select the most appropriate tool or combination of tools. For complex tasks, you can break down the problem and use different tools step by step to solve it. After using each tool, clearly explain the execution results and suggest the next steps.

If you want to stop the interaction at any point, use the `terminate` or provide a final answer.
"""

class BrowserContextHelper:
    def __init__(self, agent: "Agent"):
        self.agent = agent
        self._current_base64_image: Optional[str] = None

    async def get_browser_state(self) -> Optional[Dict[str, Any]]:
        # Find the browser tool in the agent's tools
        browser_tool = self.agent.tools.get("browser")

        if not browser_tool or not hasattr(browser_tool, "get_current_state"):
            # logger.debug("Browser tool not found or missing get_current_state")
            return None

        try:
            # Helper to execute sync or async
            import asyncio
            if asyncio.iscoroutinefunction(browser_tool.get_current_state):
                 state = await browser_tool.get_current_state()
            else:
                 state = browser_tool.get_current_state()

            if state.get("error") == "Browser not initialized":
                 return None

            if state.get("error"):
                logger.debug(f"Browser state error: {state.get('error')}")
                return None

            if state.get("base64_image"):
                self._current_base64_image = state.get("base64_image")
            else:
                self._current_base64_image = None

            return state
        except Exception as e:
            logger.debug(f"Failed to get browser state: {str(e)}")
            return None

    async def format_next_step_prompt(self) -> str:
        """Gets browser state and formats the browser prompt."""
        browser_state = await self.get_browser_state()
        url_info, tabs_info, content_above_info, content_below_info = "", "", "", ""
        results_info = ""

        if browser_state and not browser_state.get("error"):
            url_info = f"URL: {browser_state.get('url', 'N/A')}\nTitle: {browser_state.get('title', 'N/A')}"
            tabs = browser_state.get("tabs", [])
            if tabs:
                tabs_info = f"\n{len(tabs)} tab(s) available"

            pixels_above = browser_state.get("pixels_above", 0)
            pixels_below = browser_state.get("pixels_below", 0)
            if pixels_above > 0:
                content_above_info = f"Content above: {pixels_above} pixels"
            if pixels_below > 0:
                content_below_info = f"Content below: {pixels_below} pixels"

            if self._current_base64_image:
                # Add image message to memory
                # Note: Gamma's memory structure supports images via the 'base64_image' param or content block
                # We need to ensure the Message format supports this or adapt.
                # The current Message model might need to be checked.

                # Check if we can add a user message with image
                image_msg = {
                    "role": "user",
                    "content": "Current browser screenshot",
                    "base64_image": self._current_base64_image
                }
                # We add this directly to memory if supported, or via agent.add_message if we extend it
                # For now, let's assume agent.add_message might not support base64 kwarg directly without update
                # So we manually append to memory for now
                self.agent.memory.append(image_msg)

                self._current_base64_image = None  # Consume the image

            return NEXT_STEP_PROMPT.format(
                url_placeholder=url_info,
                tabs_placeholder=tabs_info,
                content_above_placeholder=content_above_info,
                content_below_placeholder=content_below_info,
                results_placeholder=results_info,
            )

        # Fallback if no browser state
        return "Based on user needs, proactively select the most appropriate tool or combination of tools."
