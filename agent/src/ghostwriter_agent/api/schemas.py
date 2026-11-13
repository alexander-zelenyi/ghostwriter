"""DTOs of the HTTP contract. They change independently of `AgentReply`."""

from enum import StrEnum

from pydantic import BaseModel, Field

TELEGRAM_MAX_MESSAGE_LENGTH = 4096


class SendMessageRequest(BaseModel):
    message_id: str = Field(min_length=1, max_length=64, description="Telegram message id.")
    text: str = Field(min_length=1, max_length=TELEGRAM_MAX_MESSAGE_LENGTH)


class ReplyStatus(StrEnum):
    REPLIED = "replied"
    NO_REPLY = "no_reply"


class Reply(BaseModel):
    text: str


class MessageResponse(BaseModel):
    status: ReplyStatus
    reply: Reply | None = Field(description="Present only when status is `replied`.")


class ErrorCode(StrEnum):
    INVALID_REQUEST = "invalid_request"
    LLM_UNAVAILABLE = "llm_unavailable"
    INTERNAL_ERROR = "internal_error"


class FieldError(BaseModel):
    loc: list[str | int]
    msg: str
    type: str


class ErrorDetail(BaseModel):
    code: str = Field(
        description="`invalid_request`, `llm_unavailable`, `internal_error`, or the snake_case "
        "name of the HTTP status (`not_found`, `method_not_allowed`, ...)."
    )
    message: str
    details: list[FieldError] | None = Field(
        default=None, description="Invalid fields, for `invalid_request`."
    )


class ErrorResponse(BaseModel):
    error: ErrorDetail
