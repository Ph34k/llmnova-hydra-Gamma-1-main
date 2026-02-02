"""Tools package for the Gamma Engine.

This package contains all concrete tool implementations that extend the
agent's capabilities, including filesystem operations, shell execution,
code search, codebase mapping, browser automation, multimodal generation,
web development, and more.

Available Tools:
    Filesystem: ListFilesTool, ReadFileTool, WriteFileTool, DiffFilesTool
    Shell: ShellTool, InteractiveShellTool
    Search: CodeSearchTool, FileSearchTool
    Map: MapDirectoryTool, CodeStatsTool, MapDependenciesTool
    Browser: ReadUrlTool, InteractBrowserTool, ScreenshotTool
    Multimodal: ImageGenerationTool, SlideGenerationTool, DiagramGenerationTool
    Web Development: WebDevTool
    Terminal: RunBashTool (legacy)
"""

from .base import Tool
from .browser import BrowserInteractTool, BrowserScreenshotTool, BrowserTool
from .filesystem import (DiffFilesTool, FileWatchTool, ListFilesTool,
                         ReadFileTool, WriteFileTool)
from .map_tool import CodeStatsTool, MapDependenciesTool, MapDirectoryTool
from .multimodal_tools import (AudioGenerationTool, DiagramGenerationTool,
                               ImageGenerationTool, SlideGenerationTool)
from .plan_tool import PlanTool
from .scheduling import ScheduleTool
from .search_tool import CodeSearchTool, FileSearchTool
from .shell_tool import InteractiveShellTool, ShellTool
from .terminal import RunBashTool
from .vision import ScreenshotTool
from .web_dev import (APIGenerationTool, ComponentGenerationTool,
                      WebDevelopmentTool)

__all__ = [
    # Base
    'Tool',
    'get_all_tools',
    'get_tool_schemas',
    # Filesystem
    'ListFilesTool',
    'ReadFileTool',
    'WriteFileTool',
    'DiffFilesTool',
    'FileWatchTool',
    # Shell
    'ShellTool',
    'InteractiveShellTool',
    # Search
    'CodeSearchTool',
    'FileSearchTool',
    # Map/Visualization
    'MapDirectoryTool',
    'CodeStatsTool',
    'MapDependenciesTool',
    # Browser
    'BrowserTool',
    'BrowserInteractTool',
    'BrowserScreenshotTool',
    'ScreenshotTool',
    # Multimodal
    'ImageGenerationTool',
    'SlideGenerationTool',
    'DiagramGenerationTool',
    'AudioGenerationTool',
    'AudioGenerationTool',
    'AudioGenerationTool',
    # Web Development
    'WebDevelopmentTool',
    'ComponentGenerationTool',
    'APIGenerationTool',
    'ScheduleTool',
    'PlanTool',
    # Terminal (legacy)
    'RunBashTool',
]


def get_all_tools() -> list[Tool]:
    """Return a list of all instantiated tools."""
    return [
        ListFilesTool(),
        ReadFileTool(),
        WriteFileTool(),
        DiffFilesTool(),
        FileWatchTool(),
        ShellTool(),
        InteractiveShellTool(),
        CodeSearchTool(),
        FileSearchTool(),
        MapDirectoryTool(),
        CodeStatsTool(),
        MapDependenciesTool(),
        BrowserTool(),
        BrowserInteractTool(),
        BrowserScreenshotTool(),
        ScreenshotTool(),
            ImageGenerationTool(),
        SlideGenerationTool(),
        DiagramGenerationTool(),
        AudioGenerationTool(),
        AudioGenerationTool(),
        AudioGenerationTool(),
        AudioGenerationTool(),
        AudioGenerationTool(),
        AudioGenerationTool(),
        AudioGenerationTool(),
        AudioGenerationTool(),
        AudioGenerationTool(),
        AudioGenerationTool(),
        AudioGenerationTool(),

    AudioGenerationTool(),
        AudioGenerationTool(),
        WebDevelopmentTool(),
        ComponentGenerationTool(),
        APIGenerationTool(),
        ScheduleTool(),
        PlanTool(),
        RunBashTool(),
    ]


def get_tool_schemas() -> list[dict]:
    """Return a list of tool schemas for all tools."""
    return [tool.to_schema() for tool in get_all_tools()]
