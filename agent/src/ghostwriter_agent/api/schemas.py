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
