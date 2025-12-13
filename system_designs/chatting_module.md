# Chatting Module Design

## 1. Overview

The Chatting module enables interactive conversations with LLM agents directly from the Goose dashboard. Users configure multiple agents in `gooseapp/app.py`, then chat with them in a dedicated UI view. Conversations are stored in runtime memory (no database), with full visibility into tool calls and outputs—reusing the same message display patterns from the Testing view.

**Primary use cases:**
- Interactively test agent behavior before writing formal test cases
- Debug agent reasoning by observing real-time tool calls and responses
- Compare how different agents handle the same queries

**How it fits with existing apps:**
- New `goose/chatting/` module alongside `goose/testing/` and `goose/tooling/`
- Routes mounted at `/chatting/*` in the FastAPI app
- New "Chatting" tab in the dashboard, reusing `MessageCards` component

---

## 2. User Interface

### GooseApp Configuration

```python
# example_system/agent.py
from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel

from example_system.tools import TOOLS

SYSTEM_PROMPT = "You are a helpful assistant for Goose Outfitters..."

def get_agent(model: str | BaseChatModel):
    """Build an agent with the specified model."""
    return create_agent(
        model=model,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )
```

```python
# gooseapp/app.py
from goose import GooseApp
from example_system.agent import get_agent

app = GooseApp(
    tools=[...],
    agents=[
        {
            "name": "Goose Outfitters Agent",
            "get_agent": get_agent,
            "models": ["gpt-4o-mini", "gpt-4o"],
        },
    ],
    reload_targets=["example_system"],
)
```

**Agent config structure:**
- `name` (required): Display name in the UI
- `get_agent` (required): `Callable[[str | BaseChatModel], Agent]` - factory function that builds an agent with the specified model
- `models` (required): List of model names available for this agent

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/chatting/agents` | List configured agents |
| GET | `/chatting/agents/{agent_id}` | Get single agent details |
| GET | `/chatting/conversations` | List all conversations (in-memory) |
| POST | `/chatting/conversations` | Create new conversation |
| GET | `/chatting/conversations/{id}` | Get conversation with messages |
| DELETE | `/chatting/conversations/{id}` | Delete a conversation |
| POST | `/chatting/conversations/{id}/clear` | Clear all messages from a conversation |
| WS | `/chatting/ws/conversations/{id}` | Stream messages for a conversation |

### Frontend Views

```
┌─────────────────────────────────────────────────────────────────┐
│  Testing  │  Tooling  │  Chatting                               │
├───────────┴───────────┴─────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────────────────────────┐ │
│  │ Conversations    │  │ Agent: [weather ▼]                   │ │
│  │                  │  ├──────────────────────────────────────┤ │
│  │ ● Weather Chat   │  │                                      │ │
│  │   Sales Debug    │  │  [MessageCards - reused component]   │ │
│  │   Test Conv      │  │                                      │ │
│  │                  │  │  👤 User: What's the weather in NYC? │ │
│  │ [+ New Chat]     │  │                                      │ │
│  │                  │  │  🚀 Agent: Let me check...           │ │
│  │                  │  │     ⚙️ Tool: get_weather(loc="NYC")  │ │
│  │                  │  │     📦 Output: {"temp": 72, ...}     │ │
│  │                  │  │                                      │ │
│  │                  │  │  🚀 Agent: It's 72°F in NYC...       │ │
│  │                  │  │                                      │ │
│  └──────────────────┘  ├──────────────────────────────────────┤ │
│                        │ [Type a message...          ] [Send] │ │
│                        └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Models

### Agent Config Schema (`goose/chatting/schema.py`)

```python
from typing import Any, Callable
from pydantic import BaseModel
from langchain_core.language_models.chat_models import BaseChatModel

class AgentConfig(BaseModel):
    """Configuration for a chat-capable agent."""
    name: str
    get_agent: Callable[[str | BaseChatModel], Any]
    models: list[str]

    model_config = ConfigDict(arbitrary_types_allowed=True)
```

### Backend Schemas (`goose/chatting/api/schema.py`)

```python
from pydantic import BaseModel, Field
from goose.testing.models.messages import Message

class AgentSummary(BaseModel):
    """Agent available for chatting."""
    id: str  # UUID assigned by GooseApp
    name: str
    models: list[str]  # Available models for this agent

class ConversationSummary(BaseModel):
    """Summary of a conversation for listing."""
    id: str
    agent_id: str  # UUID of the agent
    agent_name: str  # Denormalized for display
    model: str  # Model used for this conversation
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime

class Conversation(BaseModel):
    """Full conversation with messages."""
    id: str
    agent_id: str  # UUID of the agent
    agent_name: str  # Denormalized for display
    model: str  # Model used for this conversation
    title: str
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    agent_id: str  # UUID of the agent
    model: str  # Which model to use
    title: str | None = None  # Auto-generated if not provided

class SendMessageRequest(BaseModel):
    """Request to send a message to the agent."""
    content: str

class StreamEvent(BaseModel):
    """WebSocket event for streaming."""
    type: str  # "message_start", "message_delta", "message_end", "tool_call", "tool_output", "error"
    data: dict[str, Any]
```

### GooseApp Extension (`goose/core/app.py`)

```python
import uuid

class GooseApp:
    def __init__(
        self,
        tools: Sequence[Callable[..., Any]] | None = None,
        agents: list[dict] | None = None,  # NEW - list of agent config dicts
        reload_targets: list[str] | None = None,
        reload_exclude: list[str] | None = None,
    ) -> None:
        self.tools = list(tools) if tools else []
        self.reload_targets = reload_targets or []
        self.reload_exclude = reload_exclude or []

        # NEW: Process agents - assign IDs and build lookup dict
        self._agents_by_id: dict[str, dict] = {}
        for agent_config in (agents or []):
            agent_id = str(uuid.uuid4())
            self._agents_by_id[agent_id] = {
                "id": agent_id,
                **agent_config,
            }

        # Validate unique names
        names = [a["name"] for a in self._agents_by_id.values()]
        if len(names) != len(set(names)):
            raise ValueError("Agent names must be unique")

    @property
    def agents(self) -> list[dict]:
        """Return list of agent configs with IDs."""
        return list(self._agents_by_id.values())

    def get_agent_config(self, agent_id: str) -> dict | None:
        """Get agent config by ID."""
        return self._agents_by_id.get(agent_id)
```

### Streaming Execution

When a user sends a message:

```python
# 1. Get agent config by ID (O(1) lookup)
agent_config = goose_app.get_agent_config(conversation.agent_id)
if agent_config is None:
    raise ValueError(f"Agent not found: {conversation.agent_id}")

# 2. Build fresh agent with the conversation's model
agent = agent_config["get_agent"](conversation.model)

# 3. Stream with full conversation history
messages = [msg.to_langchain() for msg in conversation.messages]
messages.append(HumanMessage(content=user_input))

for event in agent.stream({"messages": messages}, stream_mode="messages"):
    # Convert and yield to WebSocket
    ...
```

### Streaming Implementation

The agent is built fresh for each message using `get_agent(model)`. Each call receives the **full conversation history**.

**Use `stream_mode="messages"` for token-by-token streaming:**

```python
# Inside streaming executor
messages = [msg.to_langchain() for msg in conversation.messages]
messages.append(HumanMessage(content=user_input))

for event in agent.stream({"messages": messages}, stream_mode="messages"):
    # event is a tuple: (message_chunk, metadata)
    chunk, metadata = event

    if isinstance(chunk, AIMessageChunk):
        if chunk.tool_calls:
            # Agent decided to call a tool
            yield StreamEvent(type="tool_call", data={"tool_calls": chunk.tool_calls})
        elif chunk.content:
            # Token delta - partial text
            yield StreamEvent(type="token", data={"content": chunk.content})

    elif isinstance(chunk, ToolMessage):
        # Tool execution result
        yield StreamEvent(type="tool_output", data={
            "tool_name": chunk.name,
            "content": chunk.content,
        })
```

**Stream event types from LangChain:**

| LangChain Type | Event | Description |
|---------------|-------|-------------|
| `AIMessageChunk` with `content` | `token` | Partial text token (e.g., "Go", "ose", " Outfit") |
| `AIMessageChunk` with `tool_calls` | `tool_call` | Agent wants to call a tool |
| `ToolMessage` | `tool_output` | Result from tool execution |
| Final `AIMessageChunk` (empty) | `message_end` | Stream complete |

---

## 4. Implementation Structure

```
goose/chatting/
├── __init__.py           # Public exports (none for now)
├── api/
│   ├── __init__.py       # Export router
│   ├── router.py         # FastAPI routes for conversations
│   ├── schema.py         # Pydantic request/response models
│   └── streaming.py      # WebSocket streaming logic with LangChain .stream()
└── store.py              # In-memory conversation storage (runtime only, lost on restart)

web/src/
├── views/
│   └── ChattingView.tsx  # Main chatting view
├── components/
│   └── chatting/
│       ├── ConversationList.tsx   # Sidebar with conversation list
│       ├── ChatPanel.tsx          # Main chat area
│       └── MessageInput.tsx       # Input field with send button
└── api/
    └── types.ts          # Add chatting types
```

---

## 5. API Routes

```
GET    /chatting/agents                      # List available agents (with IDs)
GET    /chatting/agents/{agent_id}           # Get single agent details
GET    /chatting/conversations               # List all conversations
POST   /chatting/conversations               # Create new conversation (agent_id + model)
GET    /chatting/conversations/{id}          # Get conversation details
DELETE /chatting/conversations/{id}          # Delete conversation
POST   /chatting/conversations/{id}/clear    # Clear all messages from conversation
WS     /chatting/ws/conversations/{id}       # Stream chat messages
```

**URL-friendly agent access:**
- `GET /chatting/agents/{agent_id}` - Get agent by UUID
- Frontend can deep-link: `/chatting?agent={agent_id}` to pre-select an agent

### WebSocket Protocol

**Client → Server:**
```json
{"type": "send_message", "content": "What's the weather in NYC?"}
```

**Server → Client (streaming with `stream_mode="messages"`):**

```json
// User message echoed back
{"type": "message", "data": {"type": "human", "content": "What's the weather in NYC?"}}

// Agent starts responding - first decides to call a tool
{"type": "tool_call", "data": {"name": "get_weather", "args": {"location": "NYC"}, "id": "call_abc123"}}

// Tool execution result
{"type": "tool_output", "data": {"tool_name": "get_weather", "tool_call_id": "call_abc123", "content": "{\"temp\": 72}"}}

// Agent streams final response token-by-token
{"type": "token", "data": {"content": "The"}}
{"type": "token", "data": {"content": " weather"}}
{"type": "token", "data": {"content": " in"}}
{"type": "token", "data": {"content": " NYC"}}
{"type": "token", "data": {"content": " is"}}
{"type": "token", "data": {"content": " 72"}}
{"type": "token", "data": {"content": "°F"}}
...

// Stream complete
{"type": "message_end", "data": {}}
```

**Event types:**
| Type | Description |
|------|-------------|
| `message` | Complete message (human input echoed, or non-streaming AI) |
| `token` | Partial AI response text (for live typing effect) |
| `tool_call` | Agent initiated a tool call |
| `tool_output` | Tool execution result |
| `message_end` | AI response complete |
| `error` | Error occurred |

---

## 6. Frontend Components

| Component | Responsibility |
|-----------|----------------|
| `ChattingView.tsx` | Main view with conversation list sidebar and chat panel |
| `ConversationList.tsx` | List conversations, create new, delete existing |
| `ChatPanel.tsx` | Display messages using `MessageCards`, manage WebSocket connection |
| `MessageInput.tsx` | Text input with send button, disabled while agent is responding |

**Reused components:**
- `MessageCards` - Display conversation messages (human, AI, tool calls, tool outputs)
- `CodeBlock` - Render JSON tool outputs
- `LoadingDots` - Show while agent is processing

---

## 7. Integration Points

### GooseApp Connection
- Agents registered via `GooseApp(agents=[Agent(...), ...])` in `gooseapp/app.py`
- Accessed via `GooseConfig().goose_app.agents`
- Each agent must have a unique `name` (used for display and lookup)

### Conversation History
- Full message history sent to agent on each request
- Messages converted to LangChain format before calling `.stream()`
- Agent locked to conversation at creation time (cannot switch mid-conversation)

### Hot Reload Behavior
- Before each message, reload source modules (same as tooling)
- Re-fetch agent functions after reload to pick up code changes

### WebSocket Updates
- Each conversation has its own WebSocket at `/chatting/ws/conversations/{id}`
- Messages stream in real-time as the agent processes
- Tool calls and outputs appear as separate message events

### Message Format
- Reuse `Message`, `ToolCall`, `TokenUsage` from `goose.testing.models.messages`
- Frontend `MessageCards` component already handles all message types

---

## 8. Implementation Plan

### Phase 1: Backend Infrastructure ✅
- [x] Add `agents` parameter to `GooseApp` (list of dicts with `name`, `get_agent`, `models`)
- [x] Create `goose/chatting/` module structure
- [x] Implement in-memory `ConversationStore` class (runtime only)
- [x] Create Pydantic schemas for API (AgentSummary, Conversation, etc.)
- [x] Implement REST endpoints (list agents with models, CRUD conversations)

**Exit Criteria:** `GET /chatting/agents` returns configured agents with names and available models, can create/list/delete conversations via REST API.

---

### Phase 2: WebSocket Streaming ✅
- [x] Implement WebSocket endpoint for conversations
- [x] Build agent using `get_agent(model)` for each message
- [x] Pass full conversation history to agent
- [x] Stream using `stream_mode="messages"` for token-by-token output
- [x] Handle tool calls and outputs as separate stream events
- [x] Add hot-reload before each message

**Exit Criteria:** Can send message via WebSocket and receive streamed response with tool calls visible in real-time.

---

### Phase 3: Frontend - Basic UI ✅
- [x] Add "Chatting" tab to `App.tsx`
- [x] Create `ChattingView.tsx` with layout
- [x] Create `ConversationList.tsx` component
- [x] Create `ChatPanel.tsx` using `MessageCards`
- [x] Create `MessageInput.tsx` component
- [x] Add API client functions and types

**Exit Criteria:** Can view conversations, see messages displayed using `MessageCards`.

---

### Phase 4: Frontend - WebSocket Integration ✅
- [x] Connect `ChatPanel` to WebSocket
- [x] Handle streaming events and update UI in real-time
- [x] Show loading state while agent is processing
- [x] Handle errors and disconnections gracefully

**Exit Criteria:** Full interactive chat experience with streamed responses and visible tool calls.

---

### Phase 5: Polish & Cleanup ✅
- [x] Agent + model selector dropdowns when creating conversation
- [x] Auto-generate conversation titles from first message
- [x] Add "Clear conversation" option
- [x] Write unit tests for store and API (35 tests)
- [ ] Update README with chatting documentation

**Exit Criteria:** Feature complete, tests passing, documentation updated.
