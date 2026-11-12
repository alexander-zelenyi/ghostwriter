from collections import OrderedDict

from ghostwriter_agent.application import AgentReply


class InMemoryProcessedMessages:
    """`ProcessedMessages` adapter that keeps the last replies of each thread in memory.

    Only the newest `max_per_thread` messages of a thread are remembered: a redelivery
    arrives shortly after the original, so older entries are not needed. The number of
    threads is not limited.
    """

    def __init__(self, max_per_thread: int = 100) -> None:
        if max_per_thread < 1:
            raise ValueError("max_per_thread must be at least 1")
        self._max_per_thread = max_per_thread
        self._replies: dict[str, OrderedDict[str, AgentReply]] = {}

    async def get(self, thread_id: str, message_id: str) -> AgentReply | None:
        return self._replies.get(thread_id, {}).get(message_id)

    async def save(self, thread_id: str, message_id: str, reply: AgentReply) -> None:
        replies = self._replies.setdefault(thread_id, OrderedDict())
        replies[message_id] = reply
        replies.move_to_end(message_id)
        while len(replies) > self._max_per_thread:
            replies.popitem(last=False)
