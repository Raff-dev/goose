# Getting started

This is the default Goose onboarding path.

Use this guide when you are starting fresh or want Goose's native chat protocol as your app contract. If you already have a LangChain or LangGraph agent, use [`docs/integrations/langchain.md`](integrations/langchain.md) instead.

## 1. Install and scaffold

```bash
pip install llm-goose
npm install -g @llm-goose/dashboard-cli
goose init
```

That gives you a `gooseapp/` directory. The main file to edit is `gooseapp/app.py`.

## 2. Register a Goose-native chat agent

```python
from collections.abc import AsyncIterator

from goose import GooseApp
from goose.chatting.agent_protocol import GooseAgentEvent
from goose.chatting.api.schema import Conversation
from goose.testing.models.messages import Message


class EchoAgent:
    name = "Echo Agent"

    async def astream_goose(
        self,
        *,
        conversation: Conversation,
        messages: list[Message],
    ) -> AsyncIterator[GooseAgentEvent]:
        latest_user_message = messages[-1].content if messages else ""

        yield GooseAgentEvent(
            type="conversation_meta",
            data={"source": "getting-started"},
        )
        yield GooseAgentEvent(type="token", data={"content": "Echo: "})
        yield GooseAgentEvent(type="token", data={"content": latest_user_message})
        yield GooseAgentEvent(type="message_end")


app = GooseApp(agents=[EchoAgent()])
```

What matters:

- A chat agent is any object with a unique `name`.
- Goose calls `astream_goose(conversation=..., messages=...)` for each assistant turn.
- Yield `GooseAgentEvent` objects to stream tokens, emit tool activity, attach conversation metadata, or finish the turn.

For most agents, these event types are enough:

- `token` – stream assistant text incrementally
- `message` – send a fully-formed `Message` in one event
- `tool_call` / `tool_output` – show tool usage in chat and traces
- `conversation_meta` – persist extra metadata on the conversation
- `message_end` – end the assistant turn

## 3. Run Goose

```bash
goose api
goose-dashboard
```

Open the dashboard, pick your agent, and start chatting.

## 4. What to do next

- Add tools to `GooseApp(tools=[...])` when you want them visible in the dashboard.
- Add tests in `gooseapp/tests/` when you want expectation-based validation.
- If you are integrating an existing LangChain stack instead of building Goose-native, switch to [`docs/integrations/langchain.md`](integrations/langchain.md).
