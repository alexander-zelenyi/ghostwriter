import asyncio

from langchain_core.messages import AIMessage

from tests.conftest import ServiceFactory

MODEL_DELAY = 0.05


async def test_concurrent_messages_in_one_thread_are_processed_in_order(
    make_service: ServiceFactory,
) -> None:
    service, model = make_service(
        [AIMessage("Hi!"), AIMessage("Reply to A"), AIMessage("Reply to B")], delay=MODEL_DELAY
    )
    await service.reply("thread-1", message_id="m1", text="Hello")

    reply_a, reply_b = await asyncio.gather(
        service.reply("thread-1", message_id="m2", text="A"),
        service.reply("thread-1", message_id="m3", text="B"),
    )

    assert reply_a.text == "Reply to A"
    assert reply_b.text == "Reply to B"
    assert [message.text for message in model.calls[2][1:]] == [
        "Hello",
        "Hi!",
        "A",
        "Reply to A",
        "B",
    ]


async def test_different_threads_are_processed_in_parallel(
    make_service: ServiceFactory,
) -> None:
    service, model = make_service([AIMessage("Hi, A!"), AIMessage("Hi, B!")], delay=MODEL_DELAY)

    await asyncio.gather(
        service.reply("thread-a", message_id="m1", text="I am A"),
        service.reply("thread-b", message_id="m2", text="I am B"),
    )

    assert model.max_active_calls == 2
