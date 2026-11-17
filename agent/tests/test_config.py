import pytest
from pydantic import ValidationError

from ghostwriter_agent.config import Settings
from tests.conftest import make_settings

LLM_KEY = "sk-real-looking-llm-key"


def test_missing_setting_error_does_not_show_other_values() -> None:
    # For a missing field pydantic reports the whole input, with every other value in it.
    # Long input is cut in the middle, so check for a part of the key.
    with pytest.raises(ValidationError) as exc_info:
        Settings(LANGUAGE_MODEL_API_KEY=LLM_KEY, _env_file=None)  # type: ignore[call-arg]

    message = str(exc_info.value)
    assert "AGENT_API_TOKEN" in message
    assert "llm-key" not in message
    assert "input_value" not in message


def test_invalid_secret_error_does_not_show_the_secret() -> None:
    short_token = "short-token-value"

    with pytest.raises(ValidationError) as exc_info:
        make_settings(AGENT_API_TOKEN=short_token)

    message = str(exc_info.value)
    assert "too_short" in message
    assert short_token not in message
