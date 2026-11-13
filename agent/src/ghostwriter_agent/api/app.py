"""FastAPI application.

Run from the `agent/` directory:

    uv run fastapi dev                                              # development, with reload
    uv run uvicorn ghostwriter_agent.api.app:create_app --factory   # without the FastAPI CLI
"""

from collections.abc import AsyncGenerator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from functools import partial

from fastapi import FastAPI

from ghostwriter_agent.api.routes import router
from ghostwriter_agent.application import AgentService
from ghostwriter_agent.bootstrap import build_agent_service
from ghostwriter_agent.config import Settings

type ServiceFactory = Callable[[], AbstractAsyncContextManager[AgentService]]


def create_app(service_factory: ServiceFactory | None = None) -> FastAPI:
    """Create the app. Tests pass a `service_factory` with fakes instead of the real LLM."""
    if service_factory is None:
        settings = Settings()  # type: ignore[call-arg]  # values come from env
        service_factory = partial(build_agent_service, settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        async with service_factory() as service:
            app.state.agent_service = service
            yield

    app = FastAPI(title="Ghostwriter agent", version="0.1.0", lifespan=lifespan)
    app.include_router(router)
    return app
