"""Exception handlers: every error is returned as `ErrorResponse` with a machine-readable code."""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ghostwriter_agent.api.schemas import ErrorCode, ErrorDetail, ErrorResponse, FieldError
from ghostwriter_agent.application import AgentUnavailableError

logger = logging.getLogger(__name__)

RETRY_AFTER_SECONDS = 30


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AgentUnavailableError, agent_unavailable_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(Exception, internal_error_handler)


def error_response(
    status: HTTPStatus,
    code: str,
    message: str,
    *,
    details: list[FieldError] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(error=ErrorDetail(code=code, message=message, details=details))
    return JSONResponse(
        body.model_dump(mode="json", exclude_none=True), status_code=status, headers=headers
    )


async def agent_unavailable_handler(request: Request, exc: AgentUnavailableError) -> JSONResponse:
    logger.warning("Language model failed: %r", exc.__cause__)
    return error_response(
        HTTPStatus.SERVICE_UNAVAILABLE,
        ErrorCode.LLM_UNAVAILABLE,
        "The language model is temporarily unavailable.",
        headers={"Retry-After": str(RETRY_AFTER_SECONDS)},
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Only location, message and type: the rejected input itself is not echoed back.
    details = [
        FieldError(loc=list(error["loc"]), msg=error["msg"], type=error["type"])
        for error in exc.errors()
    ]
    return error_response(
        HTTPStatus.UNPROCESSABLE_ENTITY,
        ErrorCode.INVALID_REQUEST,
        "The request is invalid.",
        details=details,
    )


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Errors raised as `HTTPException` (unknown path, wrong method, later 401)."""
    status = HTTPStatus(exc.status_code)
    code = status.phrase.lower().replace(" ", "_")  # 404 -> "not_found"
    return error_response(status, code, str(exc.detail), headers=exc.headers)


async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(
        HTTPStatus.INTERNAL_SERVER_ERROR,
        ErrorCode.INTERNAL_ERROR,
        "Internal server error.",
    )
