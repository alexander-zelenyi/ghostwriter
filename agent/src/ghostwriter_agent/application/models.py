from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AgentReply:
    text: str | None  # The agent's answer, or None if the conversation was finished without one.
    is_finished: bool  # True if the graph reached END (e.g. the user sent the quit command).
