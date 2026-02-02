from typing import Any, Dict, List, Optional
import logging

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from .base import Tool

# Playwright is optional - graceful degradation
try:
    from playwright.sync_api import Browser, Page, sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright not available. BrowserTool will be limited to basic HTTP requests.")

logger = logging.getLogger(__name__)

class PageContent(BaseModel):
    """Represents the content and metadata of a web page."""
    url: str
    title: Optional[str] = None
    text_content: Optional[str] = None
    html_content: Optional[str] = None
    relevant_links: List[str] = Field(default_factory=list)

class BrowserTool(Tool):
    """
    A comprehensive browser tool for headless web navigation and interaction.
    Uses Playwright for advanced features like JavaScript execution, element interaction,
    and screenshots. Falls back to simple HTTP requests for basic content reading if
    Playwright is not available or not required for the action.
    """

    def __init__(self):
        super().__init__(
            name="browser",
            description=(
                "Interact with web pages: navigate to URLs, click elements, type text, "
                "take screenshots, get element text/HTML, and extract page content. "
                "Requires Playwright for interactive actions. "
                "Actions: 'navigate', 'click', 'type', 'screenshot', 'get_text', 'get_html'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["navigate", "click", "type", "screenshot", "get_text", "get_html"],
                        "description": "The action to perform: navigate, click, type, screenshot, get_text, get_html."
                    },
                    "url": {
                        "type": "string",
                        "description": "The URL to visit or interact with (required for 'navigate', 'screenshot')."
                    },
                    "selector": {
                        "type": "string",
                        "description": "CSS selector for the element to interact with (required for 'click', 'type', 'get_text', 'get_html')."
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to type into an element (required for 'type')."
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path to save the screenshot (required for 'screenshot')."
                    },
                    "full_page": {
                        "type": "boolean",
                        "description": "Whether to capture full page for screenshot. Defaults to False."
                    },
                    "wait_for_selector": {
                        "type": "string",
                        "description": "Optional CSS selector to wait for before performing action."
                    },
                    "intent": {
                        "type": "string",
                        "enum": ["informational", "transactional", "navigational"],
                        "description": "Purpose of navigation: informational, transactional, or navigational (for 'navigate')."
                    },
                    "focus": {
                        "type": "string",
                        "description": "A description of what the agent is looking for on the page (for 'navigate')."
                    }
                },
                "required": ["action"]
            }
        )
        self._playwright_context = None
        self._browser_instance = None
        self._page_instance = None

    def _ensure_playwright_page(self, url: Optional[str] = None) -> Optional[Page]:
        """Ensures Playwright is initialized and returns a page instance."""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright is not available. Cannot perform interactive browser actions.")
            return None
        
        if not self._playwright_context:
            self._playwright_context = sync_playwright().start()
            self._browser_instance = self._playwright_context.chromium.launch(headless=True)
            self._page_instance = self._browser_instance.new_page()
            logger.info("Playwright browser and page initialized.")
        
        if url and self._page_instance.url != url:
            try:
                self._page_instance.goto(url, wait_until="networkidle")
                logger.info(f"Navigated Playwright to: {url}")
            except Exception as e:
                logger.error(f"Error navigating Playwright to {url}: {e}")
                return None
        
        return self._page_instance

    def _close_playwright(self):
        """Closes the Playwright browser instance."""
        if self._browser_instance:
            self._browser_instance.close()
            self._browser_instance = None
        if self._playwright_context:
            self._playwright_context.stop()
            self._playwright_context = None
        logger.info("Playwright browser closed.")

    def _wait_for_selector(self, page: Page, selector: str):
        """Helper to wait for a selector."""
        try:
            page.wait_for_selector(selector, timeout=10000)
            logger.debug(f"Waited for selector: {selector}")
        except Exception as e:
            logger.warning(f"Selector '{selector}' not found within timeout: {e}")

    def navigate(self, url: str, intent: Optional[str] = None, focus: Optional[str] = None, wait_for_selector: Optional[str] = None) -> PageContent:
        """
        Navigates to a URL and returns its processed content.
        
        Args:
            url: The URL to visit.
            intent: Purpose of navigation (informational, transactional, navigational).
            focus: Description of what the agent is looking for on the page.
            wait_for_selector: Optional CSS selector to wait for.
            
        Returns:
            PageContent object with extracted information.
        """
        logger.info(f"Navigating to {url} with intent '{intent}' and focus '{focus}'")
        
        if PLAYWRIGHT_AVAILABLE:
            page = self._ensure_playwright_page(url)
            if not page:
                return PageContent(url=url, text_content=f"Error: Could not navigate to {url} with Playwright.")
            
            if wait_for_selector:
                self._wait_for_selector(page, wait_for_selector)
            
            html_content = page.content()
            current_url = page.url
            title = page.title()
            
        else:
            logger.warning("Playwright not available. Falling back to requests for navigation.")
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (GammaAI)'}
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                html_content = response.text
                current_url = url
                title = None # requests doesn't easily get title
            except Exception as e:
                return PageContent(url=url, text_content=f"Error navigating with requests: {e}")

        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Pre-processing: Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text()
        
        # Compress whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_content = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Extract relevant links (simple example)
        relevant_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith('http')]
        
        # Token optimization: Selective reading based on focus (placeholder)
        if focus:
            logger.info(f"Applying focus '{focus}' for token optimization (placeholder).")
            # In a real implementation, an LLM would process 'text_content' based on 'focus'
            # to extract only the most relevant parts, or use a vision model.
            
        return PageContent(
            url=current_url,
            title=title,
            text_content=text_content[:5000] + "\n...[Content Truncated]..." if len(text_content) > 5000 else text_content,
            html_content=html_content,
            relevant_links=relevant_links
        )

    def click(self, selector: str, url: Optional[str] = None, wait_for_selector: Optional[str] = None) -> str:
        """
        Clicks an element on the current or specified page.
        
        Args:
            selector: CSS selector of the element to click.
            url: Optional URL to navigate to before clicking.
            wait_for_selector: Optional CSS selector to wait for before clicking.
            
        Returns:
            A message indicating success or failure.
        """
        page = self._ensure_playwright_page(url)
        if not page:
            return "Error: Playwright not available or navigation failed."
        
        if wait_for_selector:
            self._wait_for_selector(page, wait_for_selector)
            
try:
            page.click(selector)
            logger.info(f"Clicked element: {selector}")
            return f"Successfully clicked element: {selector}"
        except Exception as e:
            logger.error(f"Error clicking element '{selector}': {e}")
            return f"Error clicking element '{selector}': {e}"

    def type(self, selector: str, text: str, url: Optional[str] = None, wait_for_selector: Optional[str] = None) -> str:
        """
        Types text into an input field on the current or specified page.
        
        Args:
            selector: CSS selector of the input field.
            text: The text to type.
            url: Optional URL to navigate to before typing.
            wait_for_selector: Optional CSS selector to wait for before typing.
            
        Returns:
            A message indicating success or failure.
        """
        page = self._ensure_playwright_page(url)
        if not page:
            return "Error: Playwright not available or navigation failed."
        
        if wait_for_selector:
            self._wait_for_selector(page, wait_for_selector)
            
try:
            page.fill(selector, text)
            logger.info(f"Typed '{text}' into element: {selector}")
            return f"Successfully typed into element: {selector}"
        except Exception as e:
            logger.error(f"Error typing into element '{selector}': {e}")
            return f"Error typing into element '{selector}': {e}"

    def screenshot(self, output_path: str, url: Optional[str] = None, full_page: bool = False, wait_for_selector: Optional[str] = None) -> str:
        """
        Takes a screenshot of the current or specified page.
        
        Args:
            output_path: Path to save the screenshot (e.g., 'screenshot.png').
            url: Optional URL to navigate to before taking screenshot.
            full_page: Whether to capture full page or just viewport.
            wait_for_selector: Optional CSS selector to wait for before taking screenshot.
            
        Returns:
            A message indicating success or failure with the path.
        """
        page = self._ensure_playwright_page(url)
        if not page:
            return "Error: Playwright not available or navigation failed."
        
        if wait_for_selector:
            self._wait_for_selector(page, wait_for_selector)
            
try:
            page.screenshot(path=output_path, full_page=full_page)
            logger.info(f"Screenshot saved to: {output_path}")
            return f"Screenshot saved to: {output_path}"
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return f"Error taking screenshot: {e}"

    def get_text(self, selector: str, url: Optional[str] = None, wait_for_selector: Optional[str] = None) -> str:
        """
        Gets the text content of an element on the current or specified page.
        
        Args:
            selector: CSS selector of the element.
            url: Optional URL to navigate to before getting text.
            wait_for_selector: Optional CSS selector to wait for before getting text.
            
        Returns:
            The text content of the element or an error message.
        """
        page = self._ensure_playwright_page(url)
        if not page:
            return "Error: Playwright not available or navigation failed."
        
        if wait_for_selector:
            self._wait_for_selector(page, wait_for_selector)
            
try:
            text_content = page.locator(selector).text_content()
            logger.info(f"Got text from '{selector}': {text_content[:100]}...")
            return text_content if text_content is not None else ""
        except Exception as e:
            logger.error(f"Error getting text from '{selector}': {e}")
            return f"Error getting text from '{selector}': {e}"

    def get_html(self, selector: str, url: Optional[str] = None, wait_for_selector: Optional[str] = None) -> str:
        """
        Gets the inner HTML of an element on the current or specified page.
        
        Args:
            selector: CSS selector of the element.
            url: Optional URL to navigate to before getting HTML.
            wait_for_selector: Optional CSS selector to wait for before getting HTML.
            
        Returns:
            The inner HTML of the element or an error message.
        """
        page = self._ensure_playwright_page(url)
        if not page:
            return "Error: Playwright not available or navigation failed."
        
        if wait_for_selector:
            self._wait_for_selector(page, wait_for_selector)
            
try:
            html_content = page.locator(selector).inner_html()
            logger.info(f"Got HTML from '{selector}': {html_content[:100]}...")
            return html_content if html_content is not None else ""
        except Exception as e:
            logger.error(f"Error getting HTML from '{selector}': {e}")
            return f"Error getting HTML from '{selector}': {e}"

    def execute(self, action: str, **kwargs) -> Any:
        """
        Executes the specified browser action.
        """
        if action == "navigate":
            return self.navigate(**kwargs)
        elif action == "click":
            return self.click(**kwargs)
        elif action == "type":
            return self.type(**kwargs)
        elif action == "screenshot":
            return self.screenshot(**kwargs)
        elif action == "get_text":
            return self.get_text(**kwargs)
        elif action == "get_html":
            return self.get_html(**kwargs)
        else:
            return f"Error: Unknown browser action '{action}'"

    def __del__(self):
        """Ensures Playwright browser is closed when the tool is destroyed."""
        self._close_playwright()


