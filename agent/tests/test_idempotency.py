import asyncio

import pytest
from langchain_core.messages import AIMessage

from ghostwriter_agent.application import AgentUnavailableError
from tests.conftest import ServiceFactory
from tests.fakes import FakeLLMError


async def test_redelivered_message_gets_the_saved_reply_without_calling_the_llm(
    make_service: ServiceFactory,
) -> None:
    service, model = make_service([AIMessage("Hi!")])

    first = await service.reply("thread-1", message_id="m1", text="Hello")
    second = await service.reply("thread-1", message_id="m1", text="Hello")

    assert second == first
    assert len(model.calls) == 1


async def test_concurrent_duplicates_call_the_llm_once(make_service: ServiceFactory) -> None:
    service, model = make_service([AIMessage("Hi!")], delay=0.05)

    first, second = await asyncio.gather(
        service.reply("thread-1", message_id="m1", text="Hello"),
        service.reply("thread-1", message_id="m1", text="Hello"),
    )

    assert first == second
    assert first.text == "Hi!"
    assert len(model.calls) == 1


async def test_same_message_id_in_another_thread_is_not_a_duplicate(
    make_service: ServiceFactory,
) -> None:
    service, model = make_service([AIMessage("Hi, A!"), AIMessage("Hi, B!")])

    await service.reply("thread-a", message_id="m1", text="I am A")
    reply = await service.reply("thread-b", message_id="m1", text="I am B")

    assert reply.text == "Hi, B!"
    assert len(model.calls) == 2


async def test_failed_message_is_processed_again_without_duplicating_history(
    make_service: ServiceFactory,
) -> None:
    service, model = make_service(
        [AIMessage("Hi!"), FakeLLMError("LLM is down"), AIMessage("Fine, thanks.")]
    )
    await service.reply("thread-1", message_id="m1", text="Hello")

    with pytest.raises(AgentUnavailableError):
        await service.reply("thread-1", message_id="m2", text="How are you?")
    reply = await service.reply("thread-1", message_id="m2", text="How are you?")

    assert reply.text == "Fine, thanks."
    assert [message.text for message in model.calls[2][1:]] == ["Hello", "Hi!", "How are you?"]
