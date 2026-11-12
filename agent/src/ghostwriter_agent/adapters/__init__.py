"""Adapters: concrete implementations of ports and of external integrations."""

from ghostwriter_agent.adapters.clock import SystemClock
from ghostwriter_agent.adapters.llm import create_chat_model
from ghostwriter_agent.adapters.processed_messages import InMemoryProcessedMessages
from ghostwriter_agent.adapters.prompts import YamlPromptReader

__all__ = ["InMemoryProcessedMessages", "SystemClock", "YamlPromptReader", "create_chat_model"]
