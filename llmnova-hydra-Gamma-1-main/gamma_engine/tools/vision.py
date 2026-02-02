import base64
from typing import Any

from playwright.sync_api import sync_playwright

from .base import Tool


class ScreenshotTool(Tool):
    def __init__(self):
        super().__init__(
            name="screenshot",
            description="Takes a screenshot of a URL. Returns a base64 string.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to screenshot."
                    }
                },
                "required": ["url"]
            }
        )

    def execute(self, url: str, **kwargs: Any) -> str:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url)
                screenshot_bytes = page.screenshot()
                browser.close()

                # Encode to base64 for LLM vision models
                base64_img = base64.b64encode(screenshot_bytes).decode('utf-8')
                return f"data:image/png;base64,{base64_img}"
        except Exception as e:
            return f"Error taking screenshot: {str(e)}"
