"""
CLI Entry Point - Uses Terminal Adapter
"""
import asyncio
import os

from dotenv import load_dotenv

from gamma_engine.adapters.terminal_adapter import TerminalAdapter
from gamma_engine.core.llm import LLMProvider
from gamma_engine.tools.filesystem import (ListFilesTool, ReadFileTool,
                                           WriteFileTool)
from gamma_engine.tools.terminal import RunBashTool

load_dotenv()


async def main() -> None:
    """Main CLI entry point."""
    # Initialize dependencies
    llm_provider = LLMProvider(model=os.getenv("LLM_MODEL", "gpt-4o"))
    tools = [
        ListFilesTool(),
        ReadFileTool(),
        WriteFileTool(),
        RunBashTool()
    ]

    # Create terminal adapter
    adapter = TerminalAdapter(llm_provider=llm_provider, tools=tools)
    
    # Run interactive session
    await adapter.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
