"""Test doubles for the ports and the chat model."""

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field


class FixedClock:
    def __init__(self, moment: datetime) -> None:
        self._moment = moment

    def now(self) -> datetime:
        return self._moment


class ScriptedChatModel(BaseChatModel):
    """Chat model that returns pre-defined responses and records what it was sent."""

    responses: list[AIMessage]
    calls: list[list[BaseMessage]] = Field(default_factory=list)
    bound_tool_names: list[str] = Field(default_factory=list)

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
        return ChatResult(generations=[ChatGeneration(message=self.responses.pop(0))])
