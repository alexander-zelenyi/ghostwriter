from typing import Annotated

from fastapi import APIRouter, Path

from ghostwriter_agent.api.dependencies import AgentServiceDep
from ghostwriter_agent.api.schemas import (
    ErrorResponse,
    MessageResponse,
    Reply,
    ReplyStatus,
    SendMessageRequest,
)
from ghostwriter_agent.application import AgentReply

router = APIRouter(prefix="/v1")

ThreadId = Annotated[str, Path(min_length=1, max_length=128, description="One conversation.")]


@router.post(
    "/threads/{thread_id}/messages",
    responses={
        422: {"model": ErrorResponse, "description": "Invalid request (`invalid_request`)."},
        503: {
            "model": ErrorResponse,
            "description": "The language model failed (`llm_unavailable`). "
            "The message is not marked as processed: retry after `Retry-After` seconds.",
        },
    },
)
async def send_message(
    thread_id: ThreadId, body: SendMessageRequest, service: AgentServiceDep
) -> MessageResponse:
    """Send a message to the conversation and get the agent's reply.

    Repeating a request with the same `message_id` returns the same reply.
    """
    reply = await service.reply(thread_id, message_id=body.message_id, text=body.text)
    return to_response(reply)


def to_response(reply: AgentReply) -> MessageResponse:
    if not reply.text:
        return MessageResponse(status=ReplyStatus.NO_REPLY, reply=None)
    return MessageResponse(status=ReplyStatus.REPLIED, reply=Reply(text=reply.text))
