"""Runtime dependencies of the agent.

The context is passed to every graph invocation (`graph.ainvoke(..., context=...)`)
and is available in nodes as `runtime.context` and in tools as `runtime.context`
(via `ToolRuntime`). It holds only abstractions: the concrete adapters are chosen
in `ghostwriter_agent.bootstrap`, the composition root.

Rule of thumb for what goes where:
- things that define the *shape* of the graph (tools, checkpointer) -> `build_graph`;
- things the graph *uses* while running (models, external services) -> `AgentContext`.
"""

from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel

from ghostwriter_agent.ports import Clock, PromptReader


@dataclass(frozen=True, slots=True)
class AgentContext:
    model: BaseChatModel
    clock: Clock
    prompts: PromptReader
    owner_name: str
