from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

import httpx
import pytest
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver

from ghostwriter_agent.adapters import InMemoryProcessedMessages, YamlPromptReader
from ghostwriter_agent.api.app import create_app
from ghostwriter_agent.application import AgentService
from ghostwriter_agent.config import Settings
from ghostwriter_agent.core import AgentContext, build_graph
from ghostwriter_agent.tools import DEFAULT_TOOLS
from tests.fakes import FakeLLMError, FixedClock, ScriptedChatModel

FIXED_NOW = datetime(2026, 1, 15, 12, 30, tzinfo=UTC)
OWNER_NAME = "Alex"
# The real prompt files are used, so the tests also check that they load and render.
PROMPTS_DIR = Path(__file__).parents[1] / "prompts"
API_TOKEN = "test-token-" + "x" * 32


def make_settings(**overrides: Any) -> Settings:
    """Settings without env and `.env`. `overrides` are keyed by env names."""
    values: dict[str, Any] = {
        "LANGUAGE_MODEL_NAME": "deepseek-chat",
        "LANGUAGE_MODEL_PROVIDER": "deepseek",
        "LANGUAGE_MODEL_API_KEY": "fake-key",
        "OWNER_NAME": OWNER_NAME,
        "PROMPTS_DIR": PROMPTS_DIR,
        "AGENT_API_TOKEN": API_TOKEN,
    }
    return Settings(**{**values, **overrides}, _env_file=None)


class ServiceFactory(Protocol):
    def __call__(
        self, responses: list[AIMessage | Exception], *, delay: float = 0.0
    ) -> tuple[AgentService, ScriptedChatModel]: ...


@pytest.fixture
def make_service() -> ServiceFactory:
    """Build a fully wired service with fake adapters, the same way bootstrap does."""

    def factory(
        responses: list[AIMessage | Exception], *, delay: float = 0.0
    ) -> tuple[AgentService, ScriptedChatModel]:
        model = ScriptedChatModel(responses=responses, delay=delay)
        context = AgentContext(
            model=model,
            clock=FixedClock(FIXED_NOW),
            prompts=YamlPromptReader(PROMPTS_DIR),
            owner_name=OWNER_NAME,
        )
        graph = build_graph(tools=DEFAULT_TOOLS, checkpointer=InMemorySaver())
        service = AgentService(
            graph=graph,
            context=context,
            processed_messages=InMemoryProcessedMessages(),
            llm_errors=(FakeLLMError,),
        )
        return service, model

    return factory


@asynccontextmanager
async def api_client(
    service: AgentService, *, token: str | None = API_TOKEN, raise_app_exceptions: bool = True
) -> AsyncGenerator[httpx.AsyncClient]:
    """Client for the app wired to `service`. `ASGITransport` does not run the lifespan itself.

    `token=None` sends no `Authorization` header.
    `raise_app_exceptions=False` returns the 500 response instead of raising in the test.
    """

    @asynccontextmanager
    async def service_factory() -> AsyncGenerator[AgentService]:
        yield service

    app = create_app(make_settings(), service_factory=service_factory)
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=raise_app_exceptions)
    headers = {"Authorization": f"Bearer {token}"} if token is not None else None
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=transport, base_url="http://agent", headers=headers) as client,
    ):
        yield client
