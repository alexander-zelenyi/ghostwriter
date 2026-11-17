"""Health checks for Docker and other orchestrators. No token, outside `/v1`."""

from fastapi import APIRouter

from ghostwriter_agent.api.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/livez")
async def livez() -> HealthResponse:
    """Liveness: the process answers. Checks no dependencies."""
    return HealthResponse()


@router.get("/readyz")
async def readyz() -> HealthResponse:
    """Readiness: the agent can take requests. Does not call the LLM."""
    return HealthResponse()
