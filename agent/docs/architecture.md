# Agent architecture

The agent follows the **ports and adapters** (hexagonal) architecture: the core
contains the agent's logic and depends only on abstractions; everything that
talks to the outside world lives at the edges and is plugged in at one place.

## Layers

```
ghostwriter_agent/
├── core/          the LangGraph agent: state, nodes, routing, graph
├── ports/         Protocols for external services the core needs
├── adapters/      implementations of ports (system clock, YAML prompts, LLM, later Postgres)
├── tools/         tools the LLM can call
├── application/   AgentService (the API of the agent for the outside world) and its ports
├── config.py      settings from environment variables
└── bootstrap.py   composition root: wires adapters into the core
```

Dependency direction (arrows mean "imports"):

```
bootstrap ──> adapters ──> ports <── core <── application
    │             │                   ^           ^
    │             └───────────────────┼───────────┘  (application ports)
    └──> tools ───────────────────────┘
```

There are two kinds of ports. `ports/` holds what the core (graph, tools) needs;
`application/ports.py` holds what `AgentService` needs, such as `ProcessedMessages`.
Application ports use application types (`AgentReply`), so placing them in `ports/`
would create an import cycle `ports -> application -> core -> ports`.

`core` never imports `adapters` or `bootstrap`. That is what makes it possible to
run the whole graph in tests with fakes, and to swap DeepSeek for another provider
or the in-memory checkpointer for Postgres without touching the core.

## The graph

```
START -> agent --(tool calls)--> tools -> agent
agent --(no tool calls)--> human
human --(quit command)--> END
human --(any other message)--> agent
```

- **agent** (`core/nodes.py`): calls the LLM with the system prompt, the history
  and the bound tools.
- **tools**: LangGraph's prebuilt `ToolNode`; executes the tool calls from the last
  AI message and appends `ToolMessage`s. `agent -> tools -> agent` is the ReAct loop.
- **human**: calls `interrupt()`. The graph saves its state through the checkpointer
  and stops. It is resumed with `Command(resume=text)`; `interrupt()` then returns
  that text and the node turns it into a `HumanMessage`.

Routing lives in `core/routing.py` as plain functions of the state, so it can be read
and tested separately from the nodes.

## Dependency injection: build time vs run time

| What                         | Where it is passed           | Why                                            |
|------------------------------|------------------------------|------------------------------------------------|
| tools, checkpointer          | `build_graph(...)`           | they define the shape of the compiled graph    |
| model, clock, owner name...  | `AgentContext` on each call  | runtime dependencies the nodes and tools use   |

`AgentContext` uses LangGraph's `context_schema`: the graph is built with
`StateGraph(AgentState, context_schema=AgentContext)` and every call passes
`context=AgentContext(...)`. Nodes receive it as `runtime: Runtime[AgentContext]`,
tools as `runtime: ToolRuntime[AgentContext, AgentState]` (hidden from the LLM).

## Prompts

Prompts live outside the code, in `agent/prompts/<name>.yaml`, each file with a single
`template` key (Python `str.format` placeholders such as `{owner_name}`). The core asks for
them through the `PromptReader` port, which has one typed method per prompt
(`system_prompt(owner_name)`), so a caller cannot forget a placeholder and does not know
where prompts are stored. `YamlPromptReader` is the adapter: it validates each file with a
pydantic schema, renders the template and caches it. The directory is `PROMPTS_DIR`
(default `prompts`, relative to the working directory, like `.env`).

## Ports as templates

The `Clock` port is small on purpose: it is a template for the ports that will
come later (a chat repository on top of Postgres will follow the same path
`tool/node -> context -> port -> adapter`).

Convention: ports are `@runtime_checkable` Protocols. LangChain builds a pydantic
schema for `ToolRuntime[AgentContext, ...]`, and pydantic validates context fields
with `isinstance`, which a Protocol only supports when it is runtime-checkable.

## AgentService

`AgentService.reply(thread_id, message_id=..., text=...)` is the only thing callers need.
It reads the thread's checkpoint: if the graph is paused in `human`, the message resumes it;
otherwise a new run starts (the checkpointer still provides the earlier history).
A thread is one conversation; later the Telegram chat id will be used as the thread id.

Two guarantees for callers that retry or send messages concurrently:

- **One message at a time per thread.** Each thread has an `asyncio.Lock`; different
  threads run in parallel. The lock is in-process, so it holds for one worker and one replica.
- **Idempotency by `(thread_id, message_id)`.** A redelivered message gets the saved reply
  from `ProcessedMessages` without calling the LLM. A reply is saved only after success, so a
  failed message can be retried. The `HumanMessage` carries `id=message_id`, and
  `add_messages` replaces a message with the same id: if a failed attempt already wrote the
  message to the history, the retry does not duplicate it.

**Errors of the language model.** The provider SDK retries timeouts, 429 and 5xx itself
(`LANGUAGE_MODEL_TIMEOUT`, `LANGUAGE_MODEL_MAX_RETRIES`); retries are configured only there, not
with LangGraph's `RetryPolicy`, so attempts do not multiply. If the model still fails,
`AgentService` raises `AgentUnavailableError` (from `application/errors.py`). Which exceptions
count as model failures is decided by the LLM adapter (`adapters.LLM_ERRORS`) and passed to the
service in `bootstrap.py`, so the application layer does not import the provider SDK. Other
exceptions (bugs) are not wrapped.

## How SOLID shows up

- **S**: nodes, routing, prompts, graph assembly, settings and wiring are separate modules.
- **O**: a new tool is a new function added to `tools.DEFAULT_TOOLS`; a new provider is a
  configuration change. The core is not edited in either case.
- **L**: any `BaseChatModel` (DeepSeek, a test fake) or any `Clock` can be substituted.
- **I**: ports are small and specific (`Clock.now()`), not one large "services" interface.
- **D**: the core depends on `BaseChatModel` and `Clock`; concrete classes are chosen in
  `bootstrap.py`.
