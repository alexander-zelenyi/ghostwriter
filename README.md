# ghostwriter

[![agent CI](https://github.com/alexander-zelenyi/ghostwriter/actions/workflows/agent-ci.yml/badge.svg)](https://github.com/alexander-zelenyi/ghostwriter/actions/workflows/agent-ci.yml)

An AI assistant that answers Telegram messages on behalf of its owner,
built with [LangGraph](https://langchain-ai.github.io/langgraph/).

The plan is to connect it through Telegram Business: a bot attached to a
Telegram Premium account receives `business_message` updates and replies on
the owner's behalf.

## Repository layout

| Directory | What it is                                         | Status      |
|-----------|----------------------------------------------------|-------------|
| `agent/`  | LangGraph ReAct agent with a human-in-the-loop step | in progress |
| `bot/`    | Telegram bot that forwards messages to the agent    | planned     |

Each component is an independent Python project with its own dependencies and,
later, its own Docker image; `docker-compose.yml` at the root will run them
together with Postgres.

## Agent quick start

Requires [uv](https://docs.astral.sh/uv/).

```bash
cd agent
uv sync
cp .env.example .env              # then fill in the values
uv run pytest                     # tests run on a fake model, no API key needed
uv run python scripts/chat.py     # talk to the agent in the terminal
uv run fastapi dev                # HTTP API with reload; docs at http://127.0.0.1:8000/docs
```

Without the FastAPI CLI: `uv run uvicorn ghostwriter_agent.api.app:create_app --factory`.

Calling the API (the token is `AGENT_API_TOKEN` from `.env`):

```bash
curl -X POST http://127.0.0.1:8000/v1/threads/demo/messages   -H "Authorization: Bearer $AGENT_API_TOKEN"   -H "Content-Type: application/json"   -d '{"message_id": "1", "text": "Hi!"}'
```

In Docker (from `agent/`):

```bash
docker build -t ghostwriter-agent .
docker run --rm -p 127.0.0.1:8000:8000 --env-file .env ghostwriter-agent
```

See [agent/docs/architecture.md](agent/docs/architecture.md) for how the agent is built.
