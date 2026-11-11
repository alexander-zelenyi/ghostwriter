# ghostwriter

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
```

See [agent/docs/architecture.md](agent/docs/architecture.md) for how the agent is built.
