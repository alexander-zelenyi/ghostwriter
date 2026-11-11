from typing import Protocol, runtime_checkable


@runtime_checkable
class PromptReader(Protocol):
    """Source of the prompts the agent sends to the LLM."""

    def system_prompt(self, owner_name: str) -> str:
        """Return the system prompt of the agent node, rendered for `owner_name`."""
        ...
