import pytest
from langchain_core.messages import AIMessage
from pydantic import ValidationError

from tests.conftest import API_TOKEN, ServiceFactory, api_client, make_settings

URL = "/v1/threads/thread-1/messages"
BODY = {"message_id": "m1", "text": "Hello"}


async def test_request_without_token_is_401(make_service: ServiceFactory) -> None:
    service, model = make_service([])

    async with api_client(service, token=None) as client:
        response = await client.post(URL, json=BODY)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "unauthorized"
    assert model.calls == []


@pytest.mark.parametrize(
    "authorization",
    [
        b"Bearer wrong-token",
        f"Basic {API_TOKEN}".encode(),
        f"Bearer {API_TOKEN[:-1]}".encode(),
        "Bearer токен".encode(),
    ],
    ids=["wrong", "other-scheme", "prefix", "non-ascii"],
)
async def test_request_with_invalid_token_is_401(
    make_service: ServiceFactory, authorization: bytes
) -> None:
    service, model = make_service([])

    async with api_client(service, token=None) as client:
        response = await client.post(URL, json=BODY, headers={b"Authorization": authorization})

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "unauthorized"
    assert model.calls == []


async def test_request_with_valid_token_is_processed(make_service: ServiceFactory) -> None:
    service, _ = make_service([AIMessage("Hi!")])

    async with api_client(service, token=API_TOKEN) as client:
        response = await client.post(URL, json=BODY)

    assert response.status_code == 200


def test_short_api_token_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        make_settings(AGENT_API_TOKEN="a" * 31)

    [error] = exc_info.value.errors()
    assert error["loc"] == ("AGENT_API_TOKEN",)
    assert error["type"] == "too_short"
