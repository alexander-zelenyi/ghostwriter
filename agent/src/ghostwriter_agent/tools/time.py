from langchain.tools import ToolRuntime, tool

from ghostwriter_agent.core.context import AgentContext
from ghostwriter_agent.core.state import AgentState


@tool
def get_current_time(runtime: ToolRuntime[AgentContext, AgentState]) -> str:
    """Return the current date and time (UTC, ISO 8601)."""
    return runtime.context.clock.now().isoformat(timespec="seconds")
