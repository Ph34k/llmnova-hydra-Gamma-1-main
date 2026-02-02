# Gamma Engine - Tools Documentation

This document describes the tools available in the Gamma Engine framework.

## Filesystem Tools
- **ListFilesTool**: Lists files and directories in a given path.
- **ReadFileTool**: Reads the content of a file.
- **WriteFileTool**: Writes content to a file.
- **DiffFilesTool**: Returns the differences between two files.
- **FileWatchTool**: Monitors file changes.

## Shell & Terminal Tools
- **ShellTool**: Executes shell commands.
- **InteractiveShellTool**: Provides an interactive shell session.
- **RunBashTool**: Legacy tool for running bash commands.

## Search Tools
- **CodeSearchTool**: Searches for code patterns within the codebase.
- **FileSearchTool**: Searches for files by name or content.

## Mapping & Visualization Tools
- **MapDirectoryTool**: Maps the directory structure of the project.
- **CodeStatsTool**: Provides statistics about the codebase (lines of code, etc.).
- **MapDependenciesTool**: Visualizes code dependencies.

## Browser Tools
- **BrowserTool**: Navigates to a URL.
- **BrowserInteractTool**: Interacts with web elements.
- **BrowserScreenshotTool**: Takes a screenshot of the browser.
- **ScreenshotTool**: General screenshot tool.

## Multimodal Generation Tools
- **ImageGenerationTool**: Generates images from text descriptions.
- **SlideGenerationTool**: Generates presentation slides.
- **DiagramGenerationTool**: Generates diagrams (e.g., Mermaid).

## Web Development Tools (Phase 5)
- **WebDevelopmentTool**: Manages background dev servers and generates web pages.
- **ComponentGenerationTool**: Generates reusable UI components (React/HTML).
- **APIGenerationTool**: Generates FastAPI REST API endpoints.

## Scheduling Tools (Phase 5)
- **ScheduleTool**: Schedules background tasks using the `ScheduleManager`.

## Developer helper

- `scripts/ci_fix.ps1` — PowerShell helper script (project root) that installs/uses dev tools via `python -m` and runs formatters, type checks and tests. Use when working on this repo to apply automatic fixes and run the test-suite locally.

Note: prefer `python -m ruff` / `python -m isort` / `python -m mypy` when invoking tools on Windows to avoid platform-executable issues.
