import os
import subprocess
import time
from typing import Any, Dict, List, Optional

import psutil
import requests

from gamma_engine.tools.base import Tool

class WebDevTool(Tool):
    """
    Tool for web development tasks, specifically managing background servers
    and generating basic web structures (HTML/CSS/JS).
    """
    def __init__(self):
        self.active_servers: Dict[int, subprocess.Popen] = {}  # port -> process
        super().__init__(
            name="web_development_tool",
            description=(
                "Managing web development servers and creating basic web pages. "
                "Use this tool to start/stop servers or generate boilerplate HTML/CSS/JS files. "
                "Actions: 'start', 'stop', 'check', 'list', 'generate_page'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["start", "stop", "check", "list", "generate_page"],
                        "description": "The action to perform."
                    },
                    "command": {
                        "type": "string",
                        "description": "The command to run to start the server (required for 'start')."
                    },
                    "port": {
                        "type": "integer",
                        "description": "The port the server will run on."
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Current working directory for the command."
                    },
                    "path": {
                        "type": "string",
                        "description": "Path to create the file (required for 'generate_page')."
                    },
                    "title": {
                        "type": "string",
                        "description": "Title for the generated page."
                    }
                },
                "required": ["action"]
            }
        )

    def execute(self, action: str, **kwargs) -> str:
        if action == "start":
            return self._start_server(kwargs.get("command"), kwargs.get("port"), kwargs.get("cwd"))
        elif action == "stop":
            return self._stop_server(kwargs.get("port"))
        elif action == "check":
            return self._check_server(kwargs.get("port"))
        elif action == "list":
            return self._list_servers()
        elif action == "generate_page":
            return self._generate_page(kwargs.get("path"), kwargs.get("title"))
        else:
            return f"Unknown action: {action}"

    def _start_server(self, command: str | None, port: int | None, cwd: str | None = None) -> str:
        if not command or port is None:
            return "Error: 'command' and 'port' are required for start action."

        # If we already tracked a process for this port, check status
        if port in self.active_servers:
            proc = self.active_servers[port]
            if proc.poll() is None:
                return f"Error: A server is already registered on port {port}."
            else:
                del self.active_servers[port]

        # Quick network-level check
        if self._is_port_in_use(port):
            return f"Error: Port {port} is already in use by another process."

        try:
            # Platform-specific creation flags
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0

            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd or os.getcwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creationflags,
            )

            time.sleep(1)
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                return f"Error starting server. Process exited immediately.\nStdout: {stdout}\nStderr: {stderr}"

            self.active_servers[port] = process
            return f"Server started successfully on port {port}. PID: {process.pid}"
        except Exception as e:
            return f"Failed to start server: {e}"

    def _stop_server(self, port: int | None) -> str:
        if port is None:
            return "Error: 'port' is required for stop action."

        if port not in self.active_servers:
            return f"No server found managed by this tool on port {port}."

        process = self.active_servers[port]
        try:
            parent = psutil.Process(process.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
            
            del self.active_servers[port]
            return f"Server on port {port} stopped."
        except psutil.NoSuchProcess:
            del self.active_servers[port]
            return f"Server on port {port} was already stopped."
        except Exception as e:
            return f"Error stopping server: {e}"

    def _check_server(self, port: int | None) -> str:
        if port is None:
            return "Error: 'port' is required for check action."

        managed_status = "Not managed by WebDevelopmentTool"
        if port in self.active_servers:
            proc = self.active_servers[port]
            if proc.poll() is None:
                managed_status = "Managed and Running"
            else:
                managed_status = "Managed but Dead"

        try:
            response = requests.get(f"http://localhost:{port}", timeout=2)
            connection_status = f"Responding (Status: {response.status_code})"
        except requests.exceptions.ConnectionError:
            connection_status = "Not Responding"
        except Exception as e:
            connection_status = f"Error Checking: {e}"

        return f"Port {port}: {managed_status}. Network Check: {connection_status}."

    def _list_servers(self) -> str:
        if not self.active_servers:
            return "No active servers managed by WebDevelopmentTool."
        
        lines = ["Active managed servers:"]
        for port, proc in self.active_servers.items():
            status = "Running" if proc.poll() is None else "Dead"
            lines.append(f"- Port {port}: PID {proc.pid} ({status})")
        return "\n".join(lines)

    def _is_port_in_use(self, port: int) -> bool:
        for conn in psutil.net_connections():
             if conn.laddr.port == port:
                  return True
        return False

    def _generate_page(self, path: str | None, title: Optional[str] = None) -> str:
        if not path:
            return "Error: 'path' is required for generate_page action."
        title = title or "Gamma Web Page"
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div id="app">
        <h1>{title}</h1>
        <p>Generated by Gamma Engine.</p>
    </div>
    <script src="main.js"></script>
</body>
</html>"""
        
        css_content = """body {
    font-family: Arial, sans-serif;
    background-color: #f0f2f5;
    margin: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
}

#app {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    text-align: center;
}

h1 { color: #1a73e8; }"""
        
        js_content = """console.log('Gamma Web Page Loaded');
document.addEventListener('DOMContentLoaded', () => {
    console.log('App ready');
});"""

        try:
            base_dir = os.path.dirname(path)
            if base_dir and not os.path.exists(base_dir):
                os.makedirs(base_dir)
            
            with open(path, 'w') as f:
                f.write(html_content)
            
            # Create sibling CSS and JS files
            with open(os.path.join(base_dir, "style.css"), 'w') as f:
                f.write(css_content)
            with open(os.path.join(base_dir, "main.js"), 'w') as f:
                f.write(js_content)
                
            return f"Successfully generated web page at {path} with accompanying style.css and main.js"
        except Exception as e:
            return f"Error generating page: {e}"

class ComponentGenerationTool(Tool):
    """
    Tool for generating reusable UI components (React/HTML).
    """
    def __init__(self):
        super().__init__(
            name="component_generation_tool",
            description="Generate reusable UI components. Supports 'react' and 'html' types.",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "The name of the component."},
                    "type": {"type": "string", "enum": ["react", "html"], "description": "The type of component to generate."},
                    "props": {"type": "array", "items": {"type": "string"}, "description": "List of props (for React)."},
                    "output_path": {"type": "string", "description": "The file path to save the component."}
                },
                "required": ["name", "type", "output_path"]
            }
        )

    def execute(self, name: str, type: str, output_path: str, props: List[str] = None, **kwargs: Any) -> str:
        if type == "react":
            content = self._generate_react_component(name, props)
        else:
            content = self._generate_html_component(name)
            
        try:
            base_dir = os.path.dirname(output_path)
            if base_dir and not os.path.exists(base_dir):
                os.makedirs(base_dir)
            with open(output_path, 'w') as f:
                f.write(content)
            return f"Component {name} ({type}) generated at {output_path}"
        except Exception as e:
            return f"Error generating component: {e}"

    def _generate_react_component(self, name: str, props: List[str] = None) -> str:
        props_str = ", ".join(props) if props else ""
        content = f"import React from 'react';\n\nconst {name} = ({{ {props_str} }}) => {{\n  return (\n    <div className=\"{name.lower()}-container\">\n      <h2>{name} Component</h2>\n"
        if props_str:
            content += f"      <p>Props: {props_str}</p>\n"
        content += f"    </div>\n  );\n}};\n\nexport default {name};\n"
        return content

    def _generate_html_component(self, name: str) -> str:
        return f"""<div class="{name.lower()}-component">
    <!-- {name} Component -->
    <h2>{name}</h2>
</div>"""

class APIGenerationTool(Tool):
    """
    Tool for generating REST API endpoints using FastAPI.
    """
    def __init__(self):
        super().__init__(
            name="api_generation_tool",
            description="Generate FastAPI REST API endpoints.",
            parameters={
                "type": "object",
                "properties": {
                    "route": {"type": "string", "description": "The API route (e.g., '/items')."},
                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"], "description": "HTTP method."},
                    "output_path": {"type": "string", "description": "The file path to save the API code."}
                },
                "required": ["route", "method", "output_path"]
            }
        )

    def execute(self, route: str, method: str, output_path: str, **kwargs: Any) -> str:
        func_name = route.strip("/").replace("/", "_") or "root"
        method_decorator = method.lower()
        
        content = f"""from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

@app.{method_decorator}("{route}")
async def {method_decorator}_{func_name}():
    \"\"\"
    Auto-generated endpoint for {route}
    \"\"\"
    return {{"message": "Welcome to the {route} endpoint!", "method": "{method}"}}
"""
        try:
            base_dir = os.path.dirname(output_path)
            if base_dir and not os.path.exists(base_dir):
                os.makedirs(base_dir)
            with open(output_path, 'w') as f:
                f.write(content)
            return f"API endpoint {route} ({method}) generated at {output_path}"
        except Exception as e:
            return f"Error generating API: {e}"

# Backward compatibility
WebDevelopmentTool = WebDevTool
