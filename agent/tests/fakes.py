"""Test doubles for the ports and the chat model."""

import asyncio
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field, SkipValidation


class FakeLLMError(Exception):
    """Stands in for a provider error such as a timeout or a 5xx response."""


class FixedClock:
    def __init__(self, moment: datetime) -> None:
        self._moment = moment

    def now(self) -> datetime:
        return self._moment


class ScriptedChatModel(BaseChatModel):
    """Chat model that returns pre-defined responses and records what it was sent.

    An exception in `responses` is raised instead of answering, to simulate an LLM failure.
    """

    responses: SkipValidation[list[AIMessage | Exception]]
    delay: float = 0.0
    calls: list[list[BaseMessage]] = Field(default_factory=list)
    bound_tool_names: list[str] = Field(default_factory=list)
    active_calls: int = 0
    max_active_calls: int = 0

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> "ScriptedChatModel":
        self.bound_tool_names = [tool.name for tool in tools]
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        self.calls.append(list(messages))
        if not self.responses:
            raise AssertionError("ScriptedChatModel ran out of responses")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return ChatResult(generations=[ChatGeneration(message=response)])

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        self.active_calls += 1
        self.max_active_calls = max(self.max_active_calls, self.active_calls)
        try:
            await asyncio.sleep(self.delay)
            return self._generate(messages, stop, **kwargs)
        finally:
            self.active_calls -= 1
