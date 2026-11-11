"""Tools the agent can call. Adding a tool means adding it here, the core stays untouched."""

from langchain_core.tools import BaseTool

from ghostwriter_agent.tools.time import get_current_time

DEFAULT_TOOLS: tuple[BaseTool, ...] = (get_current_time,)

__all__ = ["DEFAULT_TOOLS", "get_current_time"]
