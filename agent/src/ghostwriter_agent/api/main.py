"""Entry point for servers that need an app object: `fastapi dev`, `fastapi run`, uvicorn."""

from ghostwriter_agent.api.app import create_app

app = create_app()
