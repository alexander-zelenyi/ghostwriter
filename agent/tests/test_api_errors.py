from langchain_core.messages import AIMessage

from tests.conftest import ServiceFactory, api_client
from tests.fakes import FakeLLMError

URL = "/v1/threads/thread-1/messages"
BODY = {"message_id": "m1", "text": "Hello"}


async def test_llm_failure_is_503_and_the_message_can_be_retried(
    make_service: ServiceFactory,
) -> None:
    service, _ = make_service([FakeLLMError("secret provider details"), AIMessage("Hi!")])

    async with api_client(service) as client:
        failed = await client.post(URL, json=BODY)
        retried = await client.post(URL, json=BODY)

    assert failed.status_code == 503
    assert failed.headers["Retry-After"] == "30"
    assert failed.json() == {
        "error": {
            "code": "llm_unavailable",
            "message": "The language model is temporarily unavailable.",
        }
    }
    assert "secret provider details" not in failed.text
    assert retried.status_code == 200
    assert retried.json()["reply"] == {"text": "Hi!"}


async def test_invalid_request_lists_the_fields_without_echoing_the_input(
    make_service: ServiceFactory,
) -> None:
    service, _ = make_service([])

    async with api_client(service) as client:
        response = await client.post(URL, json={"message_id": "m1", "text": "a" * 5000})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "invalid_request"
    assert [detail["loc"] for detail in error["details"]] == [["body", "text"]]
    assert "a" * 5000 not in response.text


async def test_unexpected_error_is_500_without_details(make_service: ServiceFactory) -> None:
    service, _ = make_service([ValueError("secret bug details")])

    async with api_client(service, raise_app_exceptions=False) as client:
        response = await client.post(URL, json=BODY)

    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Internal server error."}
    }
    assert "secret bug details" not in response.text


async def test_http_errors_use_the_same_format(make_service: ServiceFactory) -> None:
    service, _ = make_service([])

    async with api_client(service) as client:
        unknown_path = await client.get("/no-such-path")
        wrong_method = await client.get(URL)

    assert unknown_path.status_code == 404
    assert unknown_path.json()["error"]["code"] == "not_found"
    assert wrong_method.status_code == 405
    assert wrong_method.json()["error"]["code"] == "method_not_allowed"


async def test_openapi_documents_the_error_responses(make_service: ServiceFactory) -> None:
    service, _ = make_service([])

    async with api_client(service) as client:
        spec = (await client.get("/openapi.json")).json()

    responses = spec["paths"]["/v1/threads/{thread_id}/messages"]["post"]["responses"]
    for status in ("422", "503"):
        schema = responses[status]["content"]["application/json"]["schema"]
        assert schema == {"$ref": "#/components/schemas/ErrorResponse"}
