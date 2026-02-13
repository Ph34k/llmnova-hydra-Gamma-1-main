
import pytest
from unittest.mock import MagicMock, patch
from gamma_engine.tools.browser import BrowserTool

@pytest.fixture
def mock_playwright(mocker):
    return mocker.patch("gamma_engine.tools.browser.sync_playwright")

@pytest.fixture
def mock_requests(mocker):
    return mocker.patch("gamma_engine.tools.browser.requests")

def test_browser_navigate_playwright(mock_playwright):
    # Setup Playwright mocks
    mock_context = MagicMock()
    mock_browser = MagicMock()
    mock_page = MagicMock()

    mock_playwright.return_value.start.return_value = mock_context
    mock_context.chromium.launch.return_value = mock_browser
    mock_browser.new_page.return_value = mock_page

    # Mock page content
    mock_page.content.return_value = "<html><body><h1>Test</h1><a href='http://link.com'>Link</a></body></html>"
    mock_page.url = "http://example.com"
    mock_page.title.return_value = "Test Page"

    tool = BrowserTool()
    # Force Playwright available
    with patch("gamma_engine.tools.browser.PLAYWRIGHT_AVAILABLE", True):
        result = tool.execute("navigate", url="http://example.com")

    assert result.url == "http://example.com"
    assert result.title == "Test Page"
    assert "Test" in result.text_content
    assert "http://link.com" in result.relevant_links

def test_browser_navigate_requests_fallback(mock_requests):
    # Setup requests mock
    mock_response = MagicMock()
    mock_response.text = "<html><body><p>Fallback Content</p></body></html>"
    mock_response.status_code = 200
    mock_requests.get.return_value = mock_response

    tool = BrowserTool()
    # Force Playwright unavailable
    with patch("gamma_engine.tools.browser.PLAYWRIGHT_AVAILABLE", False):
        result = tool.execute("navigate", url="http://example.com")

    assert "Fallback Content" in result.text_content
    assert result.url == "http://example.com"

def test_browser_actions_click(mock_playwright):
    mock_page = MagicMock()
    mock_playwright.return_value.start.return_value.chromium.launch.return_value.new_page.return_value = mock_page

    tool = BrowserTool()
    with patch("gamma_engine.tools.browser.PLAYWRIGHT_AVAILABLE", True):
        tool._ensure_playwright_page() # Initialize
        result = tool.execute("click", selector="#btn")

    assert "Successfully clicked" in result
    mock_page.click.assert_called_with("#btn")

def test_browser_actions_type(mock_playwright):
    mock_page = MagicMock()
    mock_playwright.return_value.start.return_value.chromium.launch.return_value.new_page.return_value = mock_page

    tool = BrowserTool()
    with patch("gamma_engine.tools.browser.PLAYWRIGHT_AVAILABLE", True):
        tool._ensure_playwright_page()
        result = tool.execute("type", selector="#input", text="hello")

    assert "Successfully typed" in result
    mock_page.fill.assert_called_with("#input", "hello")

def test_browser_actions_screenshot(mock_playwright):
    mock_page = MagicMock()
    mock_playwright.return_value.start.return_value.chromium.launch.return_value.new_page.return_value = mock_page

    tool = BrowserTool()
    with patch("gamma_engine.tools.browser.PLAYWRIGHT_AVAILABLE", True):
        tool._ensure_playwright_page()
        result = tool.execute("screenshot", output_path="shot.png")

    assert "Screenshot saved" in result
    mock_page.screenshot.assert_called_with(path="shot.png", full_page=False)
