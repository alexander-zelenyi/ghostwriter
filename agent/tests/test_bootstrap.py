from langgraph.checkpoint.memory import InMemorySaver

from ghostwriter_agent.application import AgentService
from ghostwriter_agent.bootstrap import build_agent_service
from tests.conftest import make_settings


def test_llm_timeout_and_retries_have_defaults() -> None:
    llm = make_settings().llm

    assert llm.timeout == 30.0
    assert llm.max_retries == 2


async def test_build_agent_service_yields_a_service() -> None:
    async with build_agent_service(make_settings()) as service:
        assert isinstance(service, AgentService)


async def test_build_agent_service_uses_the_given_checkpointer() -> None:
    checkpointer = InMemorySaver()

    async with build_agent_service(make_settings(), checkpointer=checkpointer) as service:
        assert service._graph.checkpointer is checkpointer
