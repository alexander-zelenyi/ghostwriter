from typing import Annotated

from fastapi import Depends, Request

from ghostwriter_agent.application import AgentService


def get_agent_service(request: Request) -> AgentService:
    """The service created in the app lifespan."""
    return request.app.state.agent_service


AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]
