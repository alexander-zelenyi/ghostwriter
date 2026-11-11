"""Assembly of the agent graph."""

from collections.abc import Sequence
from functools import partial

from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from ghostwriter_agent.core.context import AgentContext
from ghostwriter_agent.core.nodes import agent_node, human_node
from ghostwriter_agent.core.routing import NodeName, route_after_agent, route_after_human
from ghostwriter_agent.core.state import AgentState

type AgentGraph = CompiledStateGraph[AgentState, AgentContext, AgentState, AgentState]


def build_graph(tools: Sequence[BaseTool], checkpointer: BaseCheckpointSaver) -> AgentGraph:
    """Build and compile the agent graph."""

    builder = StateGraph(AgentState, context_schema=AgentContext)

    builder.add_node(NodeName.AGENT, partial(agent_node, tools=tools))
    builder.add_node(NodeName.TOOLS, ToolNode(tools))
    builder.add_node(NodeName.HUMAN, human_node)

    builder.add_edge(START, NodeName.AGENT)
    builder.add_conditional_edges(
        NodeName.AGENT, route_after_agent, [NodeName.TOOLS, NodeName.HUMAN]
    )
    builder.add_edge(NodeName.TOOLS, NodeName.AGENT)
    builder.add_conditional_edges(NodeName.HUMAN, route_after_human, [NodeName.AGENT, END])

    return builder.compile(checkpointer=checkpointer)
