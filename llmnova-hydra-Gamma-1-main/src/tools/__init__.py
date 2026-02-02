"""Compatibility shim exposing tools under `src.tools` to match documentation.

This module imports the instantiated tools from `gamma_engine.tools.get_all_tools()`
and exposes them as module attributes named by each tool's `name` property.

Example:
    from src.tools import plan_tool
    await plan_tool.update(...)

This is a convenience layer so the documentation's `src.tools` imports work with
the existing `gamma_engine.tools` implementation.
"""

import sys
from importlib import import_module
from typing import Dict

# Lazy-import gamma_engine.tools then instantiate and export tools by name
try:
    mod = import_module("gamma_engine.tools")
    if hasattr(mod, "get_all_tools"):
        tools = mod.get_all_tools()
    else:
        tools = []
except Exception:
    tools = []

__all__ = []

for t in tools:
    # expose each tool instance under its name
    name = getattr(t, "name", None) or getattr(t, "__class__", t).__name__
    # convert to valid identifier if needed
    setattr(sys.modules[__name__], name, t)
    __all__.append(name)

# also expose a dict of tools
tools_by_name: Dict[str, object] = {name: getattr(sys.modules[__name__], name) for name in __all__}
__all__.append("tools_by_name")
