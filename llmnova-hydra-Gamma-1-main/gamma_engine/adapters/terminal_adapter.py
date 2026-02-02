"""Terminal Adapter for CLI usage of the Agent."""
import asyncio
from typing import List

from rich.console import Console
from rich.panel import Panel

from ..core.agent import Agent
from ..interfaces.llm_provider import LLMProviderInterface
from ..interfaces.tool import ToolInterface


class TerminalAdapter:
    """Adapter for running the Agent in a terminal with Rich UI."""

    def __init__(self, llm_provider: LLMProviderInterface, tools: List[ToolInterface]):
        self.console = Console()
        self.agent = Agent(
            llm_provider=llm_provider,
            tools=tools,
            event_callback=self._handle_event
        )

    def _handle_event(self, event_type: str, data: dict) -> None:
        """Handle events from the agent and display them in the terminal."""
        if event_type == "user_message":
            self.console.print(f"\n[bold white]User > [/bold white]{data['content']}")
        
        elif event_type == "llm_thinking":
            self.console.print("[yellow]Thinking...[/yellow]")
        
        elif event_type == "assistant_message":
            self.console.print(Panel(data["content"], title="Jules", border_style="magenta"))
        
        elif event_type == "tool_call":
            self.console.print(f"[cyan]Executing tool:[/cyan] {data['tool']}")
        
        elif event_type == "tool_result":
            # Only show result if it's not too long
            result = str(data['result'])
            if len(result) < 200:
                self.console.print(f"[dim]→ {result}[/dim]")
        
        elif event_type == "max_iterations":
            self.console.print(f"[red]Warning: Max iterations ({data['iterations']}) reached[/red]")

    async def run_interactive(self) -> None:
        """Run an interactive terminal session."""
        self.console.print("[bold green]Gamma Engine Online.[/bold green]")
        self.console.print("[dim]Type 'exit' to quit.[/dim]\n")

        while True:
            try:
                user_input = self.console.input("[bold white]User > [/bold white]")
                
                if user_input.lower() in ["exit", "quit"]:
                    break

                if not user_input.strip():
                    continue

                await self.agent.run(user_input)

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.console.print(f"[bold red]System Error:[/bold red] {e}")

        self.console.print("\n[dim]Goodbye![/dim]")
