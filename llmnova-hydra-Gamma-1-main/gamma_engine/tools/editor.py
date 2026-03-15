import os
from collections import defaultdict
from pathlib import Path
from typing import Any, DefaultDict, List, Literal, Optional, Dict

from .base import Tool

Command = Literal[
    "view",
    "create",
    "str_replace",
    "insert",
    "undo_edit",
]

SNIPPET_LINES: int = 4
MAX_RESPONSE_LEN: int = 16000
TRUNCATED_MESSAGE: str = (
    "<response clipped><NOTE>To save on context only part of this file has been shown to you. "
    "You should retry this tool after you have searched inside the file with `grep -n` "
    "in order to find the line numbers of what you are looking for.</NOTE>"
)

def maybe_truncate(
    content: str, truncate_after: Optional[int] = MAX_RESPONSE_LEN
) -> str:
    """Truncate content and append a notice if content exceeds the specified length."""
    if not truncate_after or len(content) <= truncate_after:
        return content
    return content[:truncate_after] + TRUNCATED_MESSAGE

class StrReplaceEditorTool(Tool):
    """
    Custom editing tool for viewing, creating and editing files.
    """
    def __init__(self, base_path: str = "."):
        super().__init__(
            name="str_replace_editor",
            description="""Custom editing tool for viewing, creating and editing files
* State is persistent across command calls and discussions with the user
* If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep
* The `create` command cannot be used if the specified `path` already exists as a file
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`
* The `undo_edit` command will revert the last edit made to the file at `path`

Notes for using the `str_replace` command:
* The `old_str` parameter should match EXACTLY one or more consecutive lines from the original file. Be mindful of whitespaces!
* If the `old_str` parameter is not unique in the file, the replacement will not be performed. Make sure to include enough context in `old_str` to make it unique
* The `new_str` parameter should contain the edited lines that should replace the `old_str`
""",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "description": "The commands to run. Allowed options are: `view`, `create`, `str_replace`, `insert`, `undo_edit`.",
                        "enum": ["view", "create", "str_replace", "insert", "undo_edit"],
                        "type": "string",
                    },
                    "path": {
                        "description": "Relative or absolute path to file or directory.",
                        "type": "string",
                    },
                    "file_text": {
                        "description": "Required parameter of `create` command, with the content of the file to be created.",
                        "type": "string",
                    },
                    "old_str": {
                        "description": "Required parameter of `str_replace` command containing the string in `path` to replace.",
                        "type": "string",
                    },
                    "new_str": {
                        "description": "Optional parameter of `str_replace` command containing the new string (if not given, no string will be added). Required parameter of `insert` command containing the string to insert.",
                        "type": "string",
                    },
                    "insert_line": {
                        "description": "Required parameter of `insert` command. The `new_str` will be inserted AFTER the line `insert_line` of `path`.",
                        "type": "integer",
                    },
                    "view_range": {
                        "description": "Optional parameter of `view` command when `path` points to a file. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting `[start_line, -1]` shows all lines from `start_line` to the end of the file.",
                        "items": {"type": "integer"},
                        "type": "array",
                    },
                },
                "required": ["command", "path"],
            }
        )
        self.base_path = base_path
        self._file_history: DefaultDict[str, List[str]] = defaultdict(list)

    def _resolve_path(self, path_str: str) -> Path:
        """Resolve path relative to base_path if not absolute."""
        p = Path(path_str)
        if not p.is_absolute():
            p = Path(self.base_path) / p
        return p.resolve()

    def execute(
        self,
        command: str,
        path: str,
        file_text: Optional[str] = None,
        view_range: Optional[List[int]] = None,
        old_str: Optional[str] = None,
        new_str: Optional[str] = None,
        insert_line: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Execute a file operation command."""
        try:
            full_path = self._resolve_path(path)

            # Helper to check existence safely
            exists = full_path.exists()
            is_dir = full_path.is_dir() if exists else False

            if command == "view":
                return self._view(full_path, view_range, exists, is_dir)

            elif command == "create":
                if exists:
                    return f"Error: File already exists at: {path}. Cannot overwrite files using command `create`."
                if file_text is None:
                    return "Error: Parameter `file_text` is required for command: create"

                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(file_text, encoding="utf-8")
                self._file_history[str(full_path)].append(file_text)
                return f"File created successfully at: {path}"

            elif command == "str_replace":
                if not exists:
                    return f"Error: The path {path} does not exist."
                if is_dir:
                    return f"Error: The path {path} is a directory."
                if old_str is None:
                    return "Error: Parameter `old_str` is required for command: str_replace"

                return self._str_replace(full_path, old_str, new_str)

            elif command == "insert":
                if not exists:
                    return f"Error: The path {path} does not exist."
                if is_dir:
                    return f"Error: The path {path} is a directory."
                if insert_line is None:
                    return "Error: Parameter `insert_line` is required for command: insert"
                if new_str is None:
                    return "Error: Parameter `new_str` is required for command: insert"

                return self._insert(full_path, insert_line, new_str)

            elif command == "undo_edit":
                if not exists:
                    return f"Error: The path {path} does not exist."
                if is_dir:
                    return f"Error: The path {path} is a directory."

                return self._undo_edit(full_path)

            else:
                return f"Error: Unrecognized command {command}."

        except Exception as e:
            return f"Error executing {command} on {path}: {str(e)}"

    def _view(self, path: Path, view_range: Optional[List[int]], exists: bool, is_dir: bool) -> str:
        if not exists:
            return f"Error: The path {path} does not exist."

        if is_dir:
            if view_range:
                return "Error: The `view_range` parameter is not allowed when `path` points to a directory."

            # Simple directory listing
            try:
                import subprocess
                cmd = f"find {path} -maxdepth 2 -not -path '*/.*'"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    return f"Error listing directory: {result.stderr}"
                return f"Files in {path}:\n{result.stdout}"
            except Exception as e:
                return f"Error listing directory: {e}"

        # File handling
        try:
            file_content = path.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading file: {e}"

        init_line = 1
        if view_range:
            if len(view_range) != 2:
                return "Error: Invalid `view_range`. It should be a list of two integers."

            file_lines = file_content.split("\n")
            n_lines = len(file_lines)
            init_line, final_line = view_range

            if init_line < 1 or init_line > n_lines:
                return f"Error: Invalid start line {init_line}. File has {n_lines} lines."

            if final_line != -1 and final_line > n_lines:
                return f"Error: Invalid end line {final_line}. File has {n_lines} lines."

            if final_line != -1 and final_line < init_line:
                return "Error: End line must be greater than or equal to start line."

            if final_line == -1:
                file_content = "\n".join(file_lines[init_line - 1:])
            else:
                file_content = "\n".join(file_lines[init_line - 1 : final_line])

        return self._make_output(file_content, str(path), init_line)

    def _str_replace(self, path: Path, old_str: str, new_str: Optional[str]) -> str:
        file_content = path.read_text(encoding="utf-8").expandtabs()
        old_str = old_str.expandtabs()
        new_str = new_str.expandtabs() if new_str is not None else ""

        occurrences = file_content.count(old_str)
        if occurrences == 0:
            return f"Error: old_str `{old_str}` not found in {path}."
        elif occurrences > 1:
            return f"Error: Multiple occurrences of old_str `{old_str}` found. Please be more specific."

        new_file_content = file_content.replace(old_str, new_str)

        # Save history
        self._file_history[str(path)].append(file_content)

        path.write_text(new_file_content, encoding="utf-8")

        return f"Successfully replaced text in {path}."

    def _insert(self, path: Path, insert_line: int, new_str: str) -> str:
        file_content = path.read_text(encoding="utf-8").expandtabs()
        new_str = new_str.expandtabs()
        lines = file_content.split("\n")
        n_lines = len(lines)

        if insert_line < 0 or insert_line > n_lines:
            return f"Error: insert_line {insert_line} out of range [0, {n_lines}]."

        new_lines_to_insert = new_str.split("\n")
        final_lines = lines[:insert_line] + new_lines_to_insert + lines[insert_line:]
        new_content = "\n".join(final_lines)

        self._file_history[str(path)].append(file_content)
        path.write_text(new_content, encoding="utf-8")

        return f"Successfully inserted text at line {insert_line} in {path}."

    def _undo_edit(self, path: Path) -> str:
        path_str = str(path)
        if not self._file_history[path_str]:
            return f"Error: No edit history for {path}."

        old_text = self._file_history[path_str].pop()
        path.write_text(old_text, encoding="utf-8")

        return f"Undo successful for {path}."

    def _make_output(self, content: str, descriptor: str, init_line: int = 1) -> str:
        content = maybe_truncate(content)
        lines = content.split("\n")
        numbered = "\n".join([f"{i+init_line:6}\t{line}" for i, line in enumerate(lines)])
        return f"Result for {descriptor}:\n{numbered}\n"
