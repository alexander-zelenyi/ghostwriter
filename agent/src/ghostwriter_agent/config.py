"""Application settings, read from environment variables and an optional `.env` file.

In Docker the variables come from the environment; locally from `agent/.env`
(the path is relative to the current working directory).
"""

from pathlib import Path

from pydantic import BaseModel, Field, NonNegativeInt, PositiveFloat, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseModel):
    model: str
    provider: str
    api_key: SecretStr
    timeout: PositiveFloat
    max_retries: NonNegativeInt


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_model: str = Field(validation_alias="LANGUAGE_MODEL_NAME")
    llm_provider: str = Field(validation_alias="LANGUAGE_MODEL_PROVIDER")
    llm_api_key: SecretStr = Field(validation_alias="API_TOKEN")
    llm_timeout: PositiveFloat = Field(default=30.0, validation_alias="LANGUAGE_MODEL_TIMEOUT")
    llm_max_retries: NonNegativeInt = Field(
        default=2, validation_alias="LANGUAGE_MODEL_MAX_RETRIES"
    )
    owner_name: str = Field(default="the account owner", validation_alias="OWNER_NAME")
    prompts_dir: Path = Field(default=Path("prompts"), validation_alias="PROMPTS_DIR")

    @property
    def llm(self) -> LLMSettings:
        """Only the LLM part, so the LLM adapter does not depend on unrelated settings."""
        return LLMSettings(
            model=self.llm_model,
            provider=self.llm_provider,
            api_key=self.llm_api_key,
            timeout=self.llm_timeout,
            max_retries=self.llm_max_retries,
        )
