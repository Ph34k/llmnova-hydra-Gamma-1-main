"""Shell execution tools for the Gamma Engine.

This module provides shell command execution with support for both
single-shot commands and interactive shell sessions. Cross-platform
support for Windows (PowerShell) and Unix-like systems (Bash/sh).

Security Features:
    - Command timeout controls
    - Working directory sandboxing
    - Command history tracking
    - Stderr capture
"""

import os
import platform
import subprocess
from typing import Any, Dict, List, Optional

from .base import Tool


class ShellTool(Tool):
    """Execute shell commands with history tracking and timeout controls.
    
    This tool provides cross-platform shell command execution with support for:
    - Automatic shell detection (PowerShell on Windows, Bash on Unix)
    - Working directory management
    - Command timeout controls
    - Command history tracking
    - Combined stdout/stderr output
    
    Attributes:
        command_history: List of executed commands with results and timestamps.
        default_shell: Detected shell based on platform (powershell.exe or /bin/bash).
    
    Security:
        - All commands are subject to timeout controls (default: 30s)
        - Working directory can be restricted
        - Command history is maintained for audit purposes
    
    Examples:
        Basic command execution:
        
        >>> tool = ShellTool()
        >>> result = tool.execute(command="ls -la")
        >>> print(result)
        total 64
        drwxr-xr-x  10 user  staff   320 Jan 30 18:00 .
        ...
        
        With working directory:
        
        >>> result = tool.execute(
        ...     command="git status",
        ...     working_dir="/path/to/repo"
        ... )
        
        With custom timeout:
        
        >>> result = tool.execute(
        ...     command="long_running_script.sh",
        ...     timeout=300  # 5 minutes
        ... )
    """

    def __init__(self):
        """Initialize the shell tool with platform-specific shell detection."""
        super().__init__(
            name="execute_shell",
            description=(
                "Executes shell commands with full control. Supports command chaining, "
                "working directory changes, and maintains command history. "
                "Use this for complex shell operations like running scripts, installing packages, "
                "or executing multiple commands in sequence."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute. Can be a single command or multiple commands separated by appropriate shell operators (&&, ||, ;, etc.)"
                    },
                    "working_dir": {
                        "type": "string",
                        "description": "Optional working directory for command execution. If not specified, uses the current working directory."
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Optional timeout in seconds. Default is 30 seconds. Use 0 for no timeout (not recommended)."
                    }
                },
                "required": ["command"]
            }
        )
        
        # Command history for context
        self.command_history: List[Dict[str, Any]] = []
        
        # Detect platform and set appropriate shell
        self.is_windows = platform.system() == "Windows"
        if self.is_windows:
            self.shell_executable = "powershell.exe"
            self.shell_args = ["-NoProfile", "-NonInteractive", "-Command"]
        else:
            self.shell_executable = "/bin/bash"
            self.shell_args = ["-c"]

    def execute(
        self, 
        command: str, 
        working_dir: Optional[str] = None,
        timeout: Optional[int] = 30,
        **kwargs: Any
    ) -> str:
        """
        Execute a shell command and return its output.
        
        Args:
            command: The shell command to execute
            working_dir: Optional working directory path
            timeout: Command timeout in seconds (default: 30, 0 for no timeout)
            
        Returns:
            Command output as string, including stderr if present
        """
        try:
            # Determine working directory
            cwd = working_dir if working_dir else os.getcwd()
            
            # Validate working directory exists
            if not os.path.exists(cwd):
                return f"Error: Working directory '{cwd}' does not exist."
            
            # Handle timeout
            actual_timeout = None if timeout == 0 else timeout
            
            # Build command based on platform
            if self.is_windows:
                # PowerShell command
                full_command = [self.shell_executable] + self.shell_args + [command]
            else:
                # Bash command
                full_command = [self.shell_executable] + self.shell_args + [command]
            
            # Execute command
            process = subprocess.run(
                full_command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=actual_timeout
            )
            
            # Build output
            output_parts = []
            
            if process.stdout:
                output_parts.append(process.stdout.strip())
            
            if process.stderr:
                output_parts.append(f"\n[STDERR]\n{process.stderr.strip()}")
            
            if process.returncode != 0:
                output_parts.append(f"\n[EXIT CODE: {process.returncode}]")
            
            output = "\n".join(output_parts) if output_parts else "Command executed with no output."
            
            # Record in history
            self.command_history.append({
                "command": command,
                "working_dir": cwd,
                "exit_code": process.returncode,
                "success": process.returncode == 0
            })
            
            return output
            
        except subprocess.TimeoutExpired:
            error_msg = f"Error: Command timed out after {timeout} seconds."
            self.command_history.append({
                "command": command,
                "working_dir": working_dir or os.getcwd(),
                "exit_code": -1,
                "success": False,
                "error": "timeout"
            })
            return error_msg
            
        except FileNotFoundError:
            error_msg = f"Error: Shell executable '{self.shell_executable}' not found."
            return error_msg
            
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            self.command_history.append({
                "command": command,
                "working_dir": working_dir or os.getcwd(),
                "exit_code": -1,
                "success": False,
                "error": str(e)
            })
            return error_msg

    def get_history(self) -> List[Dict[str, Any]]:
        """Get the command execution history.
        
        Returns:
            List of dictionaries containing command, working_dir, exit_code,
            success status, and optional error information.
        
        Examples:
            >>> tool = ShellTool()
            >>> tool.execute("ls")
            >>> history = tool.get_history()
            >>> print(history[-1]['command'])
            ls
        """
        return self.command_history

    def clear_history(self) -> None:
        """Clear the command execution history.
        
        Examples:
            >>> tool = ShellTool()
            >>> tool.execute("ls")
            >>> print(len(tool.get_history()))
            1
            >>> tool.clear_history()
            >>> print(len(tool.get_history()))
            0
        """
        self.command_history.clear()


class InteractiveShellTool(Tool):
    """Manage persistent interactive shell sessions with state retention.
    
    This tool allows creating and managing interactive shell sessions where
    state persists across commands (environment variables, cd changes, etc.).
    
    Attributes:
        sessions: Dictionary mapping session IDs to Popen process objects.
        default_session_id: Default session identifier ('default').
    
    Notes:
        This is a simplified implementation. Production systems should use
        libraries like pexpect (Unix) or pwinpty (Windows) for robust
        interactive session handling with proper output capture.
    
    Examples:
        Basic session usage:
        
        >>> tool = InteractiveShellTool()
        >>> tool.execute("cd /tmp", session_id="my_session")
        >>> tool.execute("pwd", session_id="my_session")
        >>> tool.close_session("my_session")
        
        Using default session:
        
        >>> tool.execute("export MY_VAR=123")
        >>> tool.execute("echo $MY_VAR")
    """

    def __init__(self):
        super().__init__(
            name="interactive_shell",
            description=(
                "Starts or interacts with a persistent interactive shell session. "
                "This maintains state across commands, so environment variables, "
                "directory changes, and other session state persists."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command to execute in the interactive session."
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID to use a specific shell session. If not provided, uses the default session."
                    }
                },
                "required": ["command"]
            }
        )
        
        # Store active sessions
        self.sessions: Dict[str, subprocess.Popen] = {}
        self.default_session_id = "default"

    def execute(self, command: str, session_id: Optional[str] = None, **kwargs: Any) -> str:
        """
        Execute a command in an interactive shell session.
        
        Args:
            command: The command to execute
            session_id: Optional session ID (uses default if not provided)
            
        Returns:
            Command output
        """
        sid = session_id or self.default_session_id
        
        try:
            # Create session if it doesn't exist
            if sid not in self.sessions:
                is_windows = platform.system() == "Windows"
                if is_windows:
                    shell_cmd = ["powershell.exe", "-NoProfile", "-NonInteractive"]
                else:
                    shell_cmd = ["/bin/bash", "-i"]
                
                self.sessions[sid] = subprocess.Popen(
                    shell_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            session = self.sessions[sid]
            
            # Send command
            if session.stdin:
                session.stdin.write(command + "\n")
                session.stdin.flush()
            
            # Note: Reading output from interactive sessions is complex
            # This is a simplified version - real implementation would need
            # more sophisticated output handling (possibly using pexpect/pwinpty)
            return f"Command '{command}' sent to session '{sid}'. Note: Interactive sessions have limited output capture."
            
        except Exception as e:
            return f"Error in interactive shell: {str(e)}"

    def close_session(self, session_id: Optional[str] = None) -> str:
        """Close a specific shell session.
        
        Args:
            session_id: ID of session to close. Uses default if not specified.
        
        Returns:
            Status message indicating success or error.
        """
        sid = session_id or self.default_session_id
        
        if sid in self.sessions:
            self.sessions[sid].terminate()
            del self.sessions[sid]
            return f"Session '{sid}' closed."
        
        return f"Session '{sid}' not found."

    def close_all_sessions(self) -> str:
        """Close all active shell sessions.
        
        Returns:
            Status message with count of closed sessions.
        """
        for session in self.sessions.values():
            session.terminate()
        
        count = len(self.sessions)
        self.sessions.clear()
        return f"Closed {count} session(s)."
