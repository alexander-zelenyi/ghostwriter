import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import SecretStr

from ghostwriter_agent.application import AgentService

bearer = HTTPBearer(description="The `AGENT_API_TOKEN` shared with the bot.")


def get_agent_service(request: Request) -> AgentService:
    """The service created in the app lifespan."""
    return request.app.state.agent_service


def require_token(
    request: Request, credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)]
) -> None:
    """Missing header or another scheme: `HTTPBearer` itself raises 401."""
    expected: SecretStr = request.app.state.api_token
    if not secrets.compare_digest(
        credentials.credentials.encode(), expected.get_secret_value().encode()
    ):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]
