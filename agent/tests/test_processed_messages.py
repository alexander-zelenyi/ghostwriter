import pytest

from ghostwriter_agent.adapters import InMemoryProcessedMessages
from ghostwriter_agent.application import AgentReply, ProcessedMessages

REPLY = AgentReply(text="Hi!", is_finished=False)


def test_adapter_implements_the_port() -> None:
    assert isinstance(InMemoryProcessedMessages(), ProcessedMessages)


async def test_unknown_message_is_not_found() -> None:
    assert await InMemoryProcessedMessages().get("thread-1", "m1") is None


async def test_saved_reply_is_returned() -> None:
    journal = InMemoryProcessedMessages()

    await journal.save("thread-1", "m1", REPLY)

    assert await journal.get("thread-1", "m1") == REPLY
    assert await journal.get("thread-2", "m1") is None


async def test_only_the_newest_messages_of_a_thread_are_kept() -> None:
    journal = InMemoryProcessedMessages(max_per_thread=2)

    for message_id in ("m1", "m2", "m3"):
        await journal.save("thread-1", message_id, REPLY)
    await journal.save("thread-2", "m1", REPLY)

    assert await journal.get("thread-1", "m1") is None
    assert await journal.get("thread-1", "m2") == REPLY
    assert await journal.get("thread-1", "m3") == REPLY
    assert await journal.get("thread-2", "m1") == REPLY


def test_limit_must_be_positive() -> None:
    with pytest.raises(ValueError):
        InMemoryProcessedMessages(max_per_thread=0)
