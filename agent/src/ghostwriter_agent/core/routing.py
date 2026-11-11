"""Node names and the functions that decide where the graph goes next."""

from enum import StrEnum
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END

from ghostwriter_agent.core.state import AgentState

QUIT_COMMAND = "\\quit"


class NodeName(StrEnum):
    AGENT = "agent"
    TOOLS = "tools"
    HUMAN = "human"


def route_after_agent(state: AgentState) -> Literal[NodeName.TOOLS, NodeName.HUMAN]:
    """ReAct step: run tools if the model asked for them, otherwise hand over to the human."""
    last_message = state.messages[-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return NodeName.TOOLS
    return NodeName.HUMAN


def route_after_human(state: AgentState) -> Literal[NodeName.AGENT, "__end__"]:
    """End the conversation on the quit command, otherwise let the agent answer."""
    last_message = state.messages[-1]
    if isinstance(last_message, HumanMessage) and last_message.text.strip() == QUIT_COMMAND:
        return END
    return NodeName.AGENT
