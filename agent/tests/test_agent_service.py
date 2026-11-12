from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.utils.function_calling import convert_to_openai_tool

from ghostwriter_agent.core import QUIT_COMMAND
from ghostwriter_agent.tools import get_current_time
from tests.conftest import FIXED_NOW, OWNER_NAME, ServiceFactory


async def test_first_message_gets_a_reply_and_waits_for_the_next_one(
    make_service: ServiceFactory,
) -> None:
    service, _ = make_service([AIMessage("Hi! How are you?")])

    reply = await service.reply("thread-1", message_id="m1", text="Hello")

    assert reply.text == "Hi! How are you?"
    assert not reply.is_finished


async def test_model_gets_system_prompt_and_tools(make_service: ServiceFactory) -> None:
    service, model = make_service([AIMessage("Hi!")])

    await service.reply("thread-1", message_id="m1", text="Hello")

    system_message, user_message = model.calls[0]
    assert isinstance(system_message, SystemMessage)
    assert OWNER_NAME in system_message.text
    assert user_message == HumanMessage("Hello", id=user_message.id)
    assert model.bound_tool_names == ["get_current_time"]


async def test_next_message_resumes_the_same_conversation(make_service: ServiceFactory) -> None:
    service, model = make_service([AIMessage("Hi!"), AIMessage("Fine, thanks.")])

    await service.reply("thread-1", message_id="m1", text="Hello")
    reply = await service.reply("thread-1", message_id="m2", text="How are you?")

    assert reply.text == "Fine, thanks."
    history = [message.text for message in model.calls[1][1:]]
    assert history == ["Hello", "Hi!", "How are you?"]


async def test_threads_are_isolated(make_service: ServiceFactory) -> None:
    service, model = make_service(
        [AIMessage("Hi, A!"), AIMessage("Hi, B!"), AIMessage("Nice to meet you too, A!")]
    )

    await service.reply("thread-a", message_id="m1", text="I am A")
    await service.reply("thread-b", message_id="m2", text="I am B")
    await service.reply("thread-a", message_id="m3", text="Nice to meet you!")

    assert [message.text for message in model.calls[0][1:]] == ["I am A"]
    assert [message.text for message in model.calls[1][1:]] == ["I am B"]
    assert [message.text for message in model.calls[2][1:]] == [
        "I am A",
        "Hi, A!",
        "Nice to meet you!",
    ]


async def test_tool_call_is_executed_and_result_goes_back_to_the_model(
    make_service: ServiceFactory,
) -> None:
    tool_call = {"name": "get_current_time", "args": {}, "id": "call-1"}
    service, model = make_service(
        [AIMessage("", tool_calls=[tool_call]), AIMessage("It is 12:30 UTC.")]
    )

    reply = await service.reply("thread-1", message_id="m1", text="What time is it?")

    assert reply.text == "It is 12:30 UTC."
    tool_message = model.calls[1][-1]
    assert isinstance(tool_message, ToolMessage)
    assert tool_message.text == FIXED_NOW.isoformat(timespec="seconds")


async def test_quit_command_finishes_the_conversation(make_service: ServiceFactory) -> None:
    service, model = make_service([AIMessage("Hi!")])

    await service.reply("thread-1", message_id="m1", text="Hello")
    reply = await service.reply("thread-1", message_id="m2", text=QUIT_COMMAND)

    assert reply.is_finished
    assert reply.text is None
    assert len(model.calls) == 1


async def test_message_after_quit_starts_a_new_run_with_the_old_history(
    make_service: ServiceFactory,
) -> None:
    service, model = make_service([AIMessage("Hi!"), AIMessage("Welcome back!")])

    await service.reply("thread-1", message_id="m1", text="Hello")
    await service.reply("thread-1", message_id="m2", text=QUIT_COMMAND)
    reply = await service.reply("thread-1", message_id="m3", text="I'm back")

    assert reply.text == "Welcome back!"
    assert not reply.is_finished
    assert [message.text for message in model.calls[1][1:]] == [
        "Hello",
        "Hi!",
        QUIT_COMMAND,
        "I'm back",
    ]


def test_tool_runtime_is_hidden_from_the_model() -> None:
    schema = convert_to_openai_tool(get_current_time)

    assert schema["function"]["parameters"].get("properties", {}) == {}
