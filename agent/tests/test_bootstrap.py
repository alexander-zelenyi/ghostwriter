from langgraph.checkpoint.memory import InMemorySaver

from ghostwriter_agent.application import AgentService
from ghostwriter_agent.bootstrap import build_agent_service
from ghostwriter_agent.config import Settings
from tests.conftest import OWNER_NAME, PROMPTS_DIR


def make_settings() -> Settings:
    return Settings(  # type: ignore[call-arg]  # fields are passed by their env aliases
        LANGUAGE_MODEL_NAME="deepseek-chat",
        LANGUAGE_MODEL_PROVIDER="deepseek",
        API_TOKEN="fake-key",
        OWNER_NAME=OWNER_NAME,
        PROMPTS_DIR=PROMPTS_DIR,
        _env_file=None,
    )


async def test_build_agent_service_yields_a_service() -> None:
    async with build_agent_service(make_settings()) as service:
        assert isinstance(service, AgentService)


async def test_build_agent_service_uses_the_given_checkpointer() -> None:
    checkpointer = InMemorySaver()

    async with build_agent_service(make_settings(), checkpointer=checkpointer) as service:
        assert service._graph.checkpointer is checkpointer
