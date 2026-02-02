import ast
import os
from pathlib import Path
from typing import List, Optional, Set, Dict, Any

from .base import Tool


class MapDirectoryTool(Tool):
    """
    Generate a visual directory tree representation of a codebase.
    Useful for understanding project structure at a glance.
    """

    def __init__(self):
        super().__init__(
            name="map_directory",
            description=(
                "Generate a visual tree representation of a directory structure. "
                "Shows files and folders in a hierarchical tree format. "
                "Useful for understanding project organization and finding files."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The directory path to map. Defaults to current directory."
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum depth to traverse. Defaults to 3."
                    },
                    "show_hidden": {
                        "type": "boolean",
                        "description": "Whether to show hidden files/directories (starting with .). Defaults to False."
                    },
                    "extensions_only": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of file extensions to include (e.g., ['.py', '.js']). Shows all if not specified."
                    }
                },
                "required": []
            }
        )

    def execute(
        self,
        path: str = ".",
        max_depth: int = 3,
        show_hidden: bool = False,
        extensions_only: Optional[List[str]] = None
    ) -> str:
        """
        Generate directory tree structure.
        
        Args:
            path: Directory to map
            max_depth: Maximum depth to show
            show_hidden: Include hidden files
            extensions_only: Filter by file extensions
            
        Returns:
            ASCII tree representation of directory structure
        """
        try:
            base_path = Path(path).resolve()
            
            if not base_path.exists():
                return f"Error: Path '{path}' does not exist."
            
            if not base_path.is_dir():
                return f"Error: Path '{path}' is not a directory."
            
            # Skip directories
            skip_dirs = {
                '__pycache__', '.git', '.svn', '.hg', 'node_modules',
                '.venv', 'venv', 'env', 'dist', 'build', '.next',
                '.pytest_cache', '.mypy_cache', 'coverage'
            }
            
            lines = [f"{base_path.name}/"]
            self._build_tree(
                base_path, 
                "", 
                lines, 
                0, 
                max_depth, 
                show_hidden, 
                extensions_only,
                skip_dirs
            )
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"Error generating directory map: {str(e)}"

    def _build_tree(
        self,
        directory: Path,
        prefix: str,
        lines: List[str],
        depth: int,
        max_depth: int,
        show_hidden: bool,
        extensions_only: Optional[List[str]],
        skip_dirs: Set[str]
    ) -> None:
        """Recursively build tree structure."""
        if depth >= max_depth:
            return
        
        try:
            # Get all items in directory
            items: List[Path] = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            
            # Filter items
            filtered_items: List[Path] = []
            for item in items:
                # Skip hidden files if requested
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                # Skip certain directories
                if item.is_dir() and item.name in skip_dirs:
                    continue
                
                # Filter by extension if specified
                if extensions_only and item.is_file():
                    if item.suffix not in extensions_only:
                        continue
                
                filtered_items.append(item)
            
            # Build tree
            for i, item in enumerate(filtered_items):
                is_last = i == len(filtered_items) - 1
                
                # Tree characters
                if is_last:
                    current_prefix = prefix + "└── "
                    next_prefix = prefix + "    "
                else:
                    current_prefix = prefix + "├── "
                    next_prefix = prefix + "│   "
                
                # Add item to lines
                if item.is_dir():
                    lines.append(f"{current_prefix}{item.name}/")
                    # Recurse into directory
                    self._build_tree(
                        item,
                        next_prefix,
                        lines,
                        depth + 1,
                        max_depth,
                        show_hidden,
                        extensions_only,
                        skip_dirs
                    )
                else:
                    # Show file size
                    size = item.stat().st_size
                    size_str = self._format_size(size)
                    lines.append(f"{current_prefix}{item.name} ({size_str})")
                    
        except PermissionError:
            lines.append(f"{prefix}[Permission Denied]")

    def _format_size(self, size: float) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}TB"


class CodeStatsTool(Tool):
    """
    Generate statistics about a codebase including file counts, line counts, and language breakdown.
    """

    def __init__(self):
        super().__init__(
            name="code_stats",
            description=(
                "Generate comprehensive statistics about a codebase including: "
                "total files, total lines of code, breakdown by language/file type, "
                "and largest files. Useful for understanding codebase size and composition."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The directory path to analyze. Defaults to current directory."
                    },
                    "include_comments": {
                        "type": "boolean",
                        "description": "Whether to include comments in line counts. Defaults to True."
                    }
                },
                "required": []
            }
        )

    def execute(
        self,
        path: str = ".",
        include_comments: bool = True
    ) -> str:
        """
        Generate codebase statistics.
        
        Args:
            path: Directory to analyze
            include_comments: Whether to count comment lines
            
        Returns:
            Formatted statistics report
        """
        try:
            base_path = Path(path).resolve()
            
            if not base_path.exists():
                return f"Error: Path '{path}' does not exist."
            
            if not base_path.is_dir():
                return f"Error: Path '{path}' is not a directory."
            
            stats: Dict[str, Any] = {
                'total_files': 0,
                'total_lines': 0,
                'by_extension': {},
                'largest_files': []
            }
            
            # Skip directories
            skip_dirs = {
                '__pycache__', '.git', '.svn', '.hg', 'node_modules',
                '.venv', 'venv', 'env', 'dist', 'build'
            }
            
            # Collect stats
            for root, dirs, files in os.walk(base_path):
                # Filter directories
                dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
                
                for filename in files:
                    if filename.startswith('.'):
                        continue
                    
                    file_path = Path(root) / filename
                    extension = file_path.suffix or 'no extension'
                    
                    try:
                        # Count lines
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            line_count = len(lines)
                        
                        stats['total_files'] += 1
                        stats['total_lines'] += line_count
                        
                        # Track by extension
                        if extension not in stats['by_extension']:
                            stats['by_extension'][extension] = {'files': 0, 'lines': 0}
                        
                        stats['by_extension'][extension]['files'] += 1
                        stats['by_extension'][extension]['lines'] += line_count
                        
                        # Track largest files
                        stats['largest_files'].append({
                            'path': str(file_path.relative_to(base_path)),
                            'lines': line_count
                        })
                        
                    except:
                        # Skip files that can't be read
                        continue
            
            # Sort largest files
            stats['largest_files'].sort(key=lambda x: x['lines'], reverse=True)
            stats['largest_files'] = stats['largest_files'][:10]
            
            # Format output
            output = [
                "━" * 60,
                "CODEBASE STATISTICS",
                "━" * 60,
                f"Total Files: {stats['total_files']:,}",
                f"Total Lines: {stats['total_lines']:,}",
                "",
                "Breakdown by File Type:",
                "─" * 60
            ]
            
            # Sort by line count
            sorted_extensions = sorted(
                stats['by_extension'].items(),
                key=lambda x: x[1]['lines'],
                reverse=True
            )
            
            for ext, data in sorted_extensions:
                output.append(
                    f"  {ext:20s} {data['files']:6,} files  {data['lines']:10,} lines"
                )
            
            output.extend([
                "",
                "Top 10 Largest Files:",
                "─" * 60
            ])
            
            for item in stats['largest_files']:
                output.append(f"  {item['lines']:6,} lines - {item['path']}")
            
            output.append("━" * 60)
            
            return "\n".join(output)
            
        except Exception as e:
            return f"Error generating statistics: {str(e)}"


class MapDependenciesTool(Tool):
    """
    Analyze and display import dependencies for Python files.
    """

    def __init__(self):
        super().__init__(
            name="map_dependencies",
            description=(
                "Analyze Python file dependencies by parsing import statements. "
                "Shows what modules/packages a file imports and where they come from. "
                "Currently supports Python files only."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the Python file to analyze."
                    }
                },
                "required": ["file_path"]
            }
        )

    def execute(self, file_path: str) -> str:
        """
        Analyze dependencies of a Python file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Formatted dependency report
        """
        try:
            path = Path(file_path).resolve()
            
            if not path.exists():
                return f"Error: File '{file_path}' does not exist."
            
            if not path.is_file():
                return f"Error: '{file_path}' is not a file."
            
            if path.suffix != '.py':
                return f"Error: '{file_path}' is not a Python file. Currently only Python is supported."
            
            # Parse file
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                return f"Error: Syntax error in file: {str(e)}"
            
            # Extract imports
            imports: Dict[str, List[str]] = {
                'standard': [],
                'third_party': [],
                'local': []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports['third_party'].append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    if module.startswith('.'):
                        imports['local'].append(module)
                    else:
                        imports['third_party'].append(module)
            
            # Format output
            output = [
                "━" * 60,
                f"DEPENDENCIES: {path.name}",
                "━" * 60,
                ""
            ]
            
            if imports['local']:
                output.extend([
                    "Local/Relative Imports:",
                    "─" * 60
                ])
                for imp in sorted(set(imports['local'])):
                    output.append(f"  {imp}")
                output.append("")
            
            if imports['third_party']:
                output.extend([
                    "External Imports:",
                    "─" * 60
                ])
                for imp in sorted(set(imports['third_party'])):
                    output.append(f"  {imp}")
                output.append("")
            
            total_imports = len(set(imports['local'] + imports['third_party']))
            output.append(f"Total unique imports: {total_imports}")
            output.append("━" * 60)
            
            return "\n".join(output)
            
        except Exception as e:
            return f"Error analyzing dependencies: {str(e)}"
