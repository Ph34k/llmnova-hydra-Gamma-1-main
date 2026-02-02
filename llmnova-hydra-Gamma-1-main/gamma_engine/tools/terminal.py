import subprocess
from typing import Any

from .base import Tool


class RunBashTool(Tool):
    def __init__(self):
        super().__init__(
            name="run_bash",
            description="Executes a bash command in the system shell.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to execute."
                    }
                },
                "required": ["command"]
            }
        )

    def execute(self, command: str, **kwargs: Any) -> str:
        try:
            # Security warning: In a real "unrestricted" agent, this is powerful.
            # We are mimicking the capabilities of the 'run_in_bash_session' tool.

            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                executable="/bin/bash"
            )

            output = process.stdout
            if process.stderr:
                output += f"\n[STDERR]\n{process.stderr}"

            return output.strip() or "Command executed with no output."
        except Exception as e:
            return f"Error executing command: {str(e)}"
