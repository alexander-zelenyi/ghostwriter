"""Development REPL for talking to the agent from a terminal.

Run from the `agent/` directory (so `.env` is found):

    uv run python scripts/chat.py
"""

import asyncio
import io
import sys
import uuid

from ghostwriter_agent.bootstrap import build_agent_service
from ghostwriter_agent.config import Settings
from ghostwriter_agent.core import QUIT_COMMAND


def use_utf8_console() -> None:
    """Read and print text as UTF-8 regardless of the system locale.

    On Windows, when stdin/stdout are pipes (IDE run consoles, `| tail`, ...),
    Python uses the locale code page (e.g. cp1252): characters outside it are
    printed as garbage or raise UnicodeEncodeError, which breaks Cyrillic replies.
    """
    for stream in (sys.stdin, sys.stdout):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")


async def main() -> None:
    use_utf8_console()
    settings = Settings()  # type: ignore[call-arg]  # values come from env
    thread_id = str(uuid.uuid4())

    async with build_agent_service(settings) as service:
        print(f"Chatting in thread {thread_id}. Type {QUIT_COMMAND} to exit.")
        while True:
            text = await asyncio.to_thread(input, "you> ")
            reply = await service.reply(thread_id, text)
            if reply.text:
                print(f"agent> {reply.text}")
            if reply.is_finished:
                break


if __name__ == "__main__":
    asyncio.run(main())
