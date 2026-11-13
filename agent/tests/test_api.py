from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from langchain_core.messages import AIMessage

from ghostwriter_agent.api.app import create_app
from ghostwriter_agent.application import AgentService
from ghostwriter_agent.core import QUIT_COMMAND
from tests.conftest import ServiceFactory, api_client

URL = "/v1/threads/thread-1/messages"


async def test_message_gets_a_reply(make_service: ServiceFactory) -> None:
    service, _ = make_service([AIMessage("Hi!")])

    async with api_client(service) as client:
        response = await client.post(URL, json={"message_id": "m1", "text": "Hello"})

    assert response.status_code == 200
    assert response.json() == {"status": "replied", "reply": {"text": "Hi!"}}


async def test_quit_command_gets_no_reply(make_service: ServiceFactory) -> None:
    service, _ = make_service([AIMessage("Hi!")])

    async with api_client(service) as client:
        await client.post(URL, json={"message_id": "m1", "text": "Hello"})
        response = await client.post(URL, json={"message_id": "m2", "text": QUIT_COMMAND})

    assert response.status_code == 200
    assert response.json() == {"status": "no_reply", "reply": None}


async def test_repeated_request_gets_the_same_reply(make_service: ServiceFactory) -> None:
    service, model = make_service([AIMessage("Hi!")])
    body = {"message_id": "m1", "text": "Hello"}

    async with api_client(service) as client:
        first = await client.post(URL, json=body)
        second = await client.post(URL, json=body)

    assert second.json() == first.json()
    assert len(model.calls) == 1


async def test_invalid_body_is_rejected(make_service: ServiceFactory) -> None:
    service, model = make_service([])

    async with api_client(service) as client:
        empty_text = await client.post(URL, json={"message_id": "m1", "text": ""})
        no_message_id = await client.post(URL, json={"text": "Hello"})
        too_long = await client.post(URL, json={"message_id": "m1", "text": "a" * 4097})

    assert empty_text.status_code == 422
    assert no_message_id.status_code == 422
    assert too_long.status_code == 422
    assert model.calls == []


async def test_lifespan_opens_and_closes_the_service(make_service: ServiceFactory) -> None:
    service, _ = make_service([])
    events: list[str] = []

    @asynccontextmanager
    async def service_factory() -> AsyncGenerator[AgentService]:
        events.append("opened")
        yield service
        events.append("closed")

    app = create_app(service_factory=service_factory)
    async with app.router.lifespan_context(app):
        assert events == ["opened"]

    assert events == ["opened", "closed"]
