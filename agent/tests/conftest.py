from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

import httpx
import pytest
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver

from ghostwriter_agent.adapters import InMemoryProcessedMessages, YamlPromptReader
from ghostwriter_agent.api.app import create_app
from ghostwriter_agent.application import AgentService
from ghostwriter_agent.core import AgentContext, build_graph
from ghostwriter_agent.tools import DEFAULT_TOOLS
from tests.fakes import FakeLLMError, FixedClock, ScriptedChatModel

FIXED_NOW = datetime(2026, 1, 15, 12, 30, tzinfo=UTC)
OWNER_NAME = "Alex"
# The real prompt files are used, so the tests also check that they load and render.
PROMPTS_DIR = Path(__file__).parents[1] / "prompts"


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
    service: AgentService, *, raise_app_exceptions: bool = True
) -> AsyncGenerator[httpx.AsyncClient]:
    """Client for the app wired to `service`. `ASGITransport` does not run the lifespan itself.

    `raise_app_exceptions=False` returns the 500 response instead of raising in the test.
    """

    @asynccontextmanager
    async def service_factory() -> AsyncGenerator[AgentService]:
        yield service

    app = create_app(service_factory=service_factory)
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=raise_app_exceptions)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=transport, base_url="http://agent") as client,
    ):
        yield client
