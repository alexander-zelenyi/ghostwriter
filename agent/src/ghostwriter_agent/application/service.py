"""Application service: the single entry point external code (CLI, HTTP API, bot) uses.

It hides LangGraph details such as checkpoints and interrupts behind
one method: "here is a message in this conversation, give me the reply".
"""

import asyncio
from collections import defaultdict

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from ghostwriter_agent.application.errors import AgentUnavailableError
from ghostwriter_agent.application.models import AgentReply
from ghostwriter_agent.application.ports import ProcessedMessages
from ghostwriter_agent.core import AgentContext, AgentGraph


class AgentService:
    def __init__(
        self,
        graph: AgentGraph,
        context: AgentContext,
        processed_messages: ProcessedMessages,
        llm_errors: tuple[type[Exception], ...],
    ) -> None:
        self._graph = graph
        self._context = context
        self._processed_messages = processed_messages
        self._llm_errors = llm_errors
        self._thread_locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def reply(self, thread_id: str, *, message_id: str, text: str) -> AgentReply:
        """Send a user message to the conversation `thread_id` and return the agent's reply.

        A thread is one conversation (later: one Telegram chat). If the graph is
        paused in the human node, the message resumes it; otherwise a new run starts
        and the checkpointer still provides the earlier history of the thread.
        Messages in the same thread are processed one at a time, in arrival order.

        `message_id` identifies the message within the thread (the Telegram message id).
        A message that was already processed is not sent to the LLM again: the saved
        reply is returned.

        Raises `AgentUnavailableError` if the language model fails; the message is not
        marked as processed, so it can be retried.
        """
        async with self._thread_locks[thread_id]:
            saved_reply = await self._processed_messages.get(thread_id, message_id)
            if saved_reply is not None:
                return saved_reply

            message = HumanMessage(content=text, id=message_id)
            try:
                reply = await self._run_graph(thread_id, message)
            except self._llm_errors as exc:
                raise AgentUnavailableError("The language model failed to answer") from exc
            await self._processed_messages.save(thread_id, message_id, reply)
            return reply

    async def _run_graph(self, thread_id: str, message: HumanMessage) -> AgentReply:
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        snapshot = await self._graph.aget_state(config)

        graph_input: Command | dict[str, list[HumanMessage]] = (
            Command(resume=message) if snapshot.interrupts else {"messages": [message]}
        )

        await self._graph.ainvoke(graph_input, config, context=self._context)

        snapshot = await self._graph.aget_state(config)
        is_finished = not snapshot.interrupts
        last_message = snapshot.values["messages"][-1]
        answer = last_message.text if isinstance(last_message, AIMessage) else None
        return AgentReply(text=answer, is_finished=is_finished)
