from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from ghostwriter_agent.config import LLMSettings


def create_chat_model(settings: LLMSettings) -> BaseChatModel:
    """Create a chat model for the configured provider.

    `init_chat_model` picks the integration package by provider name
    (e.g. "deepseek" -> langchain-deepseek), so switching providers is
    a configuration change plus installing the matching package.
    """
    return init_chat_model(
        model=settings.model,
        model_provider=settings.provider,
        api_key=settings.api_key.get_secret_value(),
    )
