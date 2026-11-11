"""Ports: interfaces (typing.Protocol) the core uses to talk to the outside world.

Adapters in `ghostwriter_agent.adapters` implement them. Protocols use structural typing,
so an adapter does not need to inherit from the port, it only needs matching methods.

Convention: every port is decorated with `@runtime_checkable`. Tools receive
`ToolRuntime[AgentContext, ...]`, and LangChain builds a pydantic schema for it;
pydantic validates context fields with `isinstance`, which a Protocol only
supports when it is runtime-checkable.
"""

from ghostwriter_agent.ports.clock import Clock
from ghostwriter_agent.ports.prompts import PromptReader

__all__ = ["Clock", "PromptReader"]
