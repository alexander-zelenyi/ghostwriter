import pytest
from langchain_core.messages import AIMessage
from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr

from ghostwriter_agent.adapters import create_chat_model
from ghostwriter_agent.application import AgentUnavailableError
from ghostwriter_agent.config import LLMSettings
from tests.conftest import ServiceFactory
from tests.fakes import FakeLLMError


async def test_llm_error_becomes_agent_unavailable(make_service: ServiceFactory) -> None:
    llm_error = FakeLLMError("timeout")
    service, _ = make_service([llm_error])

    with pytest.raises(AgentUnavailableError) as raised:
        await service.reply("thread-1", message_id="m1", text="Hello")

    assert raised.value.__cause__ is llm_error


async def test_other_errors_are_not_hidden(make_service: ServiceFactory) -> None:
    service, _ = make_service([ValueError("a bug")])

    with pytest.raises(ValueError):
        await service.reply("thread-1", message_id="m1", text="Hello")


async def test_thread_works_after_an_llm_error(make_service: ServiceFactory) -> None:
    service, _ = make_service([FakeLLMError("timeout"), AIMessage("Hi!")])

    with pytest.raises(AgentUnavailableError):
        await service.reply("thread-1", message_id="m1", text="Hello")
    reply = await service.reply("thread-1", message_id="m2", text="Hello?")

    assert reply.text == "Hi!"


def test_chat_model_gets_timeout_and_retries() -> None:
    settings = LLMSettings(
        model="deepseek-chat",
        provider="deepseek",
        api_key=SecretStr("fake-key"),
        timeout=12.5,
        max_retries=3,
    )

    model = create_chat_model(settings)

    assert isinstance(model, ChatDeepSeek)
    assert model.request_timeout == 12.5
    assert model.max_retries == 3
