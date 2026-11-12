"""Ports of the application layer: what `AgentService` needs from the outside world.

They live here rather than in `ghostwriter_agent.ports` because they use application
types (`AgentReply`); the core never sees them.
"""

from typing import Protocol, runtime_checkable

from ghostwriter_agent.application.models import AgentReply


@runtime_checkable
class ProcessedMessages(Protocol):
    """Journal of handled messages, used to answer redelivered messages idempotently."""

    async def get(self, thread_id: str, message_id: str) -> AgentReply | None:
        """Return the saved reply to `message_id`, or None if it was not processed."""
        ...

    async def save(self, thread_id: str, message_id: str, reply: AgentReply) -> None:
        """Remember the reply to a successfully processed message."""
        ...
