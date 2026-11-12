"""Graph nodes. Each node takes the state and returns a partial state update."""

from collections.abc import Sequence

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.runtime import Runtime
from langgraph.types import interrupt

from ghostwriter_agent.core.context import AgentContext
from ghostwriter_agent.core.state import AgentState

type StateUpdate = dict[str, list[AnyMessage]]


HUMAN_INPUT_REQUEST = "Waiting for the next message from the user."


async def agent_node(
    state: AgentState,
    runtime: Runtime[AgentContext],
    *,
    tools: Sequence[BaseTool],
) -> StateUpdate:
    """Call the LLM. The tool list is fixed at build time, the model comes from context."""

    context = runtime.context
    model = context.model.bind_tools(tools) if tools else context.model
    system_message = SystemMessage(context.prompts.system_prompt(owner_name=context.owner_name))
    response = await model.ainvoke([system_message, *state.messages])
    return {"messages": [response]}


def human_node(state: AgentState) -> StateUpdate:
    """Pause the graph until the next user message arrives."""

    message = interrupt(HUMAN_INPUT_REQUEST)
    if not isinstance(message, HumanMessage):
        raise TypeError(
            f"Expected the resume value to be a HumanMessage, got {type(message).__name__}"
        )
    return {"messages": [message]}
