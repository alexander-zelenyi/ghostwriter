# syntax=docker/dockerfile:1

# Both stages use the same image: .venv links to the interpreter by its absolute path.
ARG PYTHON_IMAGE=python:3.12-slim-trixie

FROM ${PYTHON_IMAGE} AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.2 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable


FROM ${PYTHON_IMAGE}

RUN useradd --system --uid 10001 --no-create-home app

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY prompts ./prompts

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER app

EXPOSE 8000

# No curl in slim images. urlopen raises on non-2xx and on timeout, so python exits with 1.
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/readyz', timeout=2)"]

# Exec form: uvicorn is PID 1 and gets SIGTERM, so the lifespan shuts down cleanly.
# One worker: the per-thread lock in AgentService is in-process.
CMD ["uvicorn", "ghostwriter_agent.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
