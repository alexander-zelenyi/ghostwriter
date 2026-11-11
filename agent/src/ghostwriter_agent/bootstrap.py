"""Composition root: the only place that knows about concrete adapters.

Everything else depends on abstractions; here they are wired together.
To swap an implementation (another LLM, a Postgres checkpointer, a fake clock)
you change this file, not the core.
"""

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver

from ghostwriter_agent.adapters import SystemClock, YamlPromptReader, create_chat_model
from ghostwriter_agent.application import AgentService
from ghostwriter_agent.config import Settings
from ghostwriter_agent.core import AgentContext, build_graph
from ghostwriter_agent.tools import DEFAULT_TOOLS


def build_agent_service(
    settings: Settings, checkpointer: BaseCheckpointSaver | None = None
) -> AgentService:
    context = AgentContext(
        model=create_chat_model(settings.llm),
        clock=SystemClock(),
        prompts=YamlPromptReader(settings.prompts_dir),
        owner_name=settings.owner_name,
    )
    graph = build_graph(tools=DEFAULT_TOOLS, checkpointer=checkpointer or InMemorySaver())
    return AgentService(graph=graph, context=context)
