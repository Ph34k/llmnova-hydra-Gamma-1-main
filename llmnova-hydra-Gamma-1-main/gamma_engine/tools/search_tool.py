"""Code and file search tools for the Gamma Engine.

This module provides powerful search capabilities including:
- Code content search with regex support (grep-like)
- File name/path search with glob patterns
- Case-sensitive and case-insensitive modes
- File type filtering
- Result limiting

These tools are essential for code navigation, finding references,
and exploratory analysis of codebases.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern

from .base import Tool


class CodeSearchTool(Tool):
    """Search through code files for specific patterns or text.
    
    This tool provides grep-like functionality with support for:
    - Plain text and regex pattern Search
    - Case-sensitive and case-insensitive modes
    - File extension filtering
    - Line number and context display
    - Result count limiting
    
    Attributes:
        name: Tool identifier 'search_code'.
        description: Human-readable description for LLM.
        parameters: JSON schema defining search parameters.
    
    Examples:
        Simple text search:
        
        >>> tool = CodeSearchTool()
        >>> results = tool.execute(
        ...     pattern="TODO",
        ...     path="src/",
        ...     case_sensitive=False
        ... )
        
        Regex search for function definitions:
        
        >>> results = tool.execute(
        ...     pattern=r"def \w+\(",
        ...     path=".",
        ...     use_regex=True,
        ...     file_extensions=[".py"]
        ... )
        
        Limited results:
        
        >>> results = tool.execute(
        ...     pattern="import",
        ...     max_results=10
        ... )
    """

    def __init__(self):
        super().__init__(
            name="search_code",
            description=(
                "Search for text or patterns within code files. Supports regex patterns, "
                "case-insensitive search, and file type filtering. Returns matching lines "
                "with line numbers and file paths. Use this to find specific code patterns, "
                "function calls, imports, or any text across the codebase."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "The text or regex pattern to search for."
                    },
                    "path": {
                        "type": "string",
                        "description": "The directory or file path to search in. Defaults to current directory."
                    },
                    "file_extensions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of file extensions to search (e.g., ['.py', '.js']). If not specified, searches all text files."
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Whether the search should be case-sensitive. Defaults to False."
                    },
                    "use_regex": {
                        "type": "boolean",
                        "description": "Whether to treat the pattern as a regex. Defaults to False (plain text search)."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return. Defaults to 50."
                    }
                },
                "required": ["pattern"]
            }
        )

    def execute(
        self,
        pattern: str,
        path: str = ".",
        file_extensions: Optional[List[str]] = None,
        case_sensitive: bool = False,
        use_regex: bool = False,
        max_results: int = 50
    ) -> str:
        """
        Search for a pattern in code files.
        
        Args:
            pattern: Text or regex pattern to search for
            path: Directory or file path to search
            file_extensions: Optional list of file extensions to filter
            case_sensitive: Whether search is case-sensitive
            use_regex: Whether to use regex matching
            max_results: Maximum number of results
            
        Returns:
            Formatted search results with file paths, line numbers, and matching lines
        """
        try:
            results: List[Dict[str, Any]] = []
            search_path = Path(path).resolve()
            
            # Validate path exists
            if not search_path.exists():
                return f"Error: Path '{path}' does not exist."
            
            # Compile regex pattern if needed
            if use_regex:
                try:
                    regex_flags = 0 if case_sensitive else re.IGNORECASE
                    compiled_pattern: Optional[Pattern] = re.compile(pattern, regex_flags)
                except re.error as e:
                    return f"Error: Invalid regex pattern: {str(e)}"
            else:
                compiled_pattern = None
            
            # Determine files to search
            if search_path.is_file():
                files_to_search = [search_path]
            else:
                files_to_search = self._get_files_to_search(search_path, file_extensions)
            
            # Search through files
            for file_path in files_to_search:
                if len(results) >= max_results:
                    break
                
                try:
                    matches = self._search_file(
                        file_path, 
                        pattern, 
                        compiled_pattern, 
                        case_sensitive
                    )
                    results.extend(matches)
                    
                    if len(results) >= max_results:
                        results = results[:max_results]
                        break
                        
                except Exception:
                    # Skip files that can't be read (binary, permissions, etc.)
                    continue
            
            # Format results
            if not results:
                return f"No matches found for pattern '{pattern}' in {path}"
            
            output_lines = [f"Found {len(results)} match(es) for '{pattern}':\n"]
            
            for match in results:
                file_rel = match['file']
                line_num = match['line_number']
                line_content = match['line'].strip()
                
                output_lines.append(f"{file_rel}:{line_num}: {line_content}")
            
            if len(results) == max_results:
                output_lines.append(f"\n... (limited to {max_results} results)")
            
            return "\n".join(output_lines)
            
        except Exception as e:
            return f"Error during search: {str(e)}"

    def _get_files_to_search(
        self, 
        base_path: Path, 
        extensions: Optional[List[str]]
    ) -> List[Path]:
        """Get list of files to search based on path and extensions."""
        files = []
        
        # Common text file extensions if none specified
        default_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
            '.cs', '.go', '.rb', '.php', '.swift', '.kt', '.rs', '.scala',
            '.html', '.css', '.scss', '.sass', '.less',
            '.json', '.yaml', '.yml', '.xml', '.toml', '.ini', '.cfg',
            '.md', '.txt', '.rst', '.tex',
            '.sh', '.bash', '.zsh', '.fish', '.ps1',
            '.sql', '.graphql', '.proto'
        }
        
        # Directories to skip
        skip_dirs = {
            '__pycache__', '.git', '.svn', '.hg', 'node_modules', 
            '.venv', 'venv', 'env', '.env', 'dist', 'build',
            '.next', '.nuxt', 'coverage', '.pytest_cache',
            '.mypy_cache', '.eggs', '*.egg-info'
        }
        
        for root, dirs, filenames in os.walk(base_path):
            # Filter out directories to skip
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
            
            for filename in filenames:
                file_path = Path(root) / filename
                file_ext = file_path.suffix
                
                # Check if file matches extension filter
                if extensions:
                    if file_ext in extensions:
                        files.append(file_path)
                else:
                    # Use default extensions
                    if file_ext in default_extensions:
                        files.append(file_path)
        
        return files

    def _search_file(
        self,
        file_path: Path,
        pattern: str,
        compiled_pattern: Optional[Pattern],
        case_sensitive: bool
    ) -> List[Dict[str, Any]]:
        """Search a single file for the pattern."""
        matches = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, start=1):
                    found = False
                    
                    if compiled_pattern:
                        # Regex search
                        found = bool(compiled_pattern.search(line))
                    else:
                        # Plain text search
                        if case_sensitive:
                            found = pattern in line
                        else:
                            found = pattern.lower() in line.lower()
                    
                    if found:
                        matches.append({
                            'file': str(file_path),
                            'line_number': line_num,
                            'line': line.rstrip('\n\r')
                        })
        except:
            # Skip files that can't be read
            pass
        
        return matches


class FileSearchTool(Tool):
    """
    Search for files by name or path pattern.
    Supports glob patterns and case-insensitive matching.
    """

    def __init__(self):
        super().__init__(
            name="find_files",
            description=(
                "Find files by name or path pattern. Supports glob patterns like '*.py' "
                "or 'test_*.js'. Use this to locate files in the codebase by name or pattern."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "File name or glob pattern to search for (e.g., '*.py', 'test_*.js', 'config.json')"
                    },
                    "path": {
                        "type": "string",
                        "description": "The directory to search in. Defaults to current directory."
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Whether the search should be case-sensitive. Defaults to False."
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum directory depth to search. Defaults to unlimited."
                    }
                },
                "required": ["pattern"]
            }
        )

    def execute(
        self,
        pattern: str,
        path: str = ".",
        case_sensitive: bool = False,
        max_depth: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """
        Search for files matching a pattern.
        
        Args:
            pattern: Glob pattern to match
            path: Directory to search
            case_sensitive: Whether search is case-sensitive
            max_depth: Maximum depth to search
            
        Returns:
            List of matching file paths
        """
        try:
            search_path = Path(path).resolve()
            
            if not search_path.exists():
                return f"Error: Path '{path}' does not exist."
            
            if not search_path.is_dir():
                return f"Error: Path '{path}' is not a directory."
            
            matches = []
            
            # Skip directories
            skip_dirs = {
                '__pycache__', '.git', '.svn', '.hg', 'node_modules',
                '.venv', 'venv', 'env', '.env', 'dist', 'build'
            }
            
            # Walk directory tree
            for root, dirs, files in os.walk(search_path):
                # Calculate current depth
                if max_depth is not None:
                    current_depth = len(Path(root).relative_to(search_path).parts)
                    if current_depth > max_depth:
                        continue
                
                # Filter out skip directories
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                
                # Check each file
                for filename in files:
                    match = False
                    
                    if case_sensitive:
                        match = Path(filename).match(pattern)
                    else:
                        match = Path(filename.lower()).match(pattern.lower())
                    
                    if match:
                        file_path = Path(root) / filename
                        matches.append(str(file_path))
            
            # Format results
            if not matches:
                return f"No files found matching pattern '{pattern}' in {path}"
            
            output_lines = [f"Found {len(matches)} file(s) matching '{pattern}':\n"]
            output_lines.extend(matches)
            
            return "\n".join(output_lines)
            
        except Exception as e:
            return f"Error during file search: {str(e)}"
