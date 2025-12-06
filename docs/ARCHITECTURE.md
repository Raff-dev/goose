# Goose Architecture Design

## Overview

Goose is a library for developing, testing, and debugging LLM agents. It provides a unified dashboard with multiple "apps" (like Django apps) that are decoupled but share common infrastructure.

## Apps

### 1. Testing (existing)
- Run behavioral tests against your agent
- Validate expectations using LLM-based evaluation
- View test results, tool calls, agent responses

### 2. Tooling (new)
- Browse tools available to your agent
- Invoke tools directly with custom arguments
- See tool results (for debugging/exploration)

### 3. Future Apps
- **Logging**: View agent execution logs
- **Chatting**: Interactive chat with your agent
- **MCP**: Manage MCP server connections

---

## Project Structure (User's Project)

Users create a `gooseapp/` folder in their project root (or use `goose init`):

```bash
# Initialize gooseapp folder with boilerplate
uv run goose init
```

```
project_root/
├── my_agent/                     # User's agent code
│   ├── agent.py
│   ├── tools.py
│   └── ...
│
├── gooseapp/                     # Goose configuration folder
│   ├── app.py                    # Central config - GooseApp
│   └── tests/
│       ├── conftest.py           # Test fixtures
│       ├── test_basic.py
│       └── test_workflows.py
│
└── pyproject.toml
```

---

## Developer Interface

### Initialization

```bash
# Creates gooseapp/ folder with starter files
uv run goose init

# Creates:
# gooseapp/
# ├── app.py          # GooseApp with placeholder
# └── tests/
#     └── conftest.py # Starter fixture
```

### GooseApp (Central Configuration)

```python
# gooseapp/app.py
from goose import GooseApp
from my_agent.tools import get_products, create_order, check_inventory

app = GooseApp(
    tools=[get_products, create_order, check_inventory],
    reload_targets=["my_agent"],
    # Future:
    # mcp_servers=[...],
)
```

### Test Fixtures

```python
# gooseapp/tests/conftest.py
from goose.testing import Goose, goose_fixture
from gooseapp.app import app
from my_agent.agent import query

@goose_fixture
def goose():
    return Goose(
        query_fn=query,
        tools=app.tools,
        validator="gpt-4o-mini",
    )
```

---

## CLI

```bash
# Initialize gooseapp folder
uv run goose init

# Start the dashboard (explicit app path)
uv run goose api --app gooseapp.app:app

# With reload targets override
uv run goose api --app gooseapp.app:app --reload-target my_agent

# Run tests (future)
uv run goose run --app gooseapp.app:app
```

### Entry Point (pyproject.toml)

```toml
[project.scripts]
goose = "goose.cli:app"
```

Single entry point replaces the old `goose-run` and `goose-api` commands.

---

## Package Structure (Goose Library)

```
goose/
├── core/                       # Shared infrastructure
│   ├── __init__.py
│   ├── app.py                  # GooseApp class
│   ├── loader.py               # Load app from module:var path
│   ├── reload.py               # Hot reload mechanism
│   └── websocket.py            # Shared WebSocket manager
│
├── api/                        # API server
│   ├── __init__.py
│   ├── app.py                  # Creates FastAPI, mounts app routers
│   └── routes.py               # Health check, app info
│
├── testing/                    # Testing app
│   ├── __init__.py
│   ├── cli.py                  # Testing subcommands
│   ├── api/
│   │   ├── router.py           # /testing/* endpoints
│   │   ├── schema.py
│   │   └── jobs/
│   ├── discovery.py
│   ├── runner.py
│   ├── validator.py
│   └── ...
│
├── tooling/                    # Tooling app (NEW)
│   ├── __init__.py
│   ├── cli.py                  # Tooling subcommands (if any)
│   ├── api/
│   │   ├── router.py           # /tooling/* endpoints
│   │   └── schema.py
│   └── executor.py             # Invoke a tool with arguments
│
└── cli.py                      # Main CLI - imports and registers app CLIs
```

### CLI Structure

Each app defines its own CLI commands, registered into the main app:

```python
# goose/testing/cli.py
import typer

app = typer.Typer(help="Run Goose tests")

@app.command()
def run(...):
    """Run tests from command line."""
    ...

@app.command()
def list(...):
    """List discovered tests."""
    ...
```

```python
# goose/cli.py
import typer
from goose.testing.cli import app as testing_app

app = typer.Typer(help="Goose - LLM agent development toolkit")

# Register app CLIs as subcommand groups
app.add_typer(testing_app, name="test")

@app.command()
def init():
    """Initialize gooseapp/ folder with starter files."""
    ...

@app.command()
def api():
    """Start the Goose dashboard server."""
    ...
```

```bash
# Commands
goose init                           # Create gooseapp/ folder
goose api --app gooseapp.app:app     # Start dashboard
goose test run gooseapp.tests        # Run tests
goose test list gooseapp.tests       # List tests
```

---

## GooseApp Class

```python
# goose/core/app.py
from typing import Callable

class GooseApp:
    """Central configuration for Goose dashboard."""

    def __init__(
        self,
        tools: list[Callable] | None = None,
        reload_targets: list[str] | None = None,
        # Future:
        # mcp_servers: list[MCPServerConfig] | None = None,
    ):
        self.tools = tools or []
        self.reload_targets = reload_targets or []
```

---

## API Routes

### Testing (`/testing/*`)
```
GET  /testing/tests              # List discovered tests
GET  /testing/runs               # List test runs
POST /testing/runs               # Start a new run
GET  /testing/runs/{id}          # Get run details
```

### Tooling (`/tooling/*`)
```
GET  /tooling/tools              # List registered tools
GET  /tooling/tools/{name}       # Get tool details + parameter schema
POST /tooling/tools/{name}/invoke  # Execute tool with arguments
```

### Shared
```
GET  /health                     # Health check
WS   /ws                         # Real-time updates (all apps)
```

---

## Frontend

Single dashboard with tab navigation:

```
┌─────────────────────────────────────────────────┐
│  🪿 Goose          [Testing] [Tooling]          │
├─────────────────────────────────────────────────┤
│                                                 │
│   (View changes based on selected tab)          │
│                                                 │
└─────────────────────────────────────────────────┘
```

```
web/src/
├── App.tsx                 # Tab navigation + routing
├── views/
│   ├── TestingView.tsx     # Current dashboard (refactored out of App.tsx)
│   └── ToolingView.tsx     # Tool browser + invoker
├── api/
│   ├── client.ts           # Shared HTTP client
│   ├── testing.ts          # /testing/* API calls
│   └── tooling.ts          # /tooling/* API calls
└── components/
    ├── testing/            # Testing-specific components
    └── tooling/            # Tooling-specific components
```

---

## Hot Reload

When files in `reload_targets` change:
1. Reload the Python modules in `reload_targets`
2. Reload `gooseapp` module (always included implicitly)
3. Re-fetch `GooseApp` instance to get updated tools list
4. Re-discover tests (testing app)
5. Push updates via WebSocket to frontend

### Tools Hot Reload

Tools are passed to `GooseApp` as function references. To ensure they update on reload:

1. `gooseapp` is always added to the reload targets automatically
2. After reload, the API re-fetches the `app` from the module (not cached)
3. Fresh `GooseApp` instance has fresh tool references

```python
# goose/core/loader.py
def get_effective_reload_targets(app: GooseApp, app_path: str) -> list[str]:
    """Get reload targets including the app module itself."""
    app_module = app_path.rsplit(":", 1)[0]  # "gooseapp.app"
    base_module = app_module.split(".")[0]   # "gooseapp"

    targets = set(app.reload_targets)
    targets.add(base_module)  # Always reload gooseapp
    return list(targets)

def get_app(app_path: str) -> GooseApp:
    """Get the current GooseApp instance (fresh after reload)."""
    module_path, var_name = app_path.rsplit(":", 1)
    module = sys.modules.get(module_path)
    if module is None:
        module = importlib.import_module(module_path)
    return getattr(module, var_name)
```

---

## Design Decisions

### 1. Tool Parameter Schema
- Extract parameters from function signature + type hints
- Display docstring in the UI
- **LangChain `@tool` decorated functions only** - no support for plain functions

### 2. Tool Invocation Context
- Just invoke the tool with provided arguments
- No environment setup - developer's responsibility
- Tools must be self-contained or handle their own connections

### 3. Route Prefixing
- **Prefix everything for consistency**
- `/testing/*` for all testing endpoints
- `/tooling/*` for all tooling endpoints
- Breaking change for existing testing routes (migration needed)

### 4. Async Tools
- Executor supports both sync and async tool functions
- Detect if tool is async and await accordingly

### 5. Frontend Navigation
- **Tabs at the top**
- Clean, simple navigation between apps

---

## Implementation Plan

**Important**: Each phase must end with all tests passing (`make test`). Add tests for new/changed behavior.

### Phase 1: Core Infrastructure ✅
**Goal**: Create shared foundation for all apps

- [x] Create `goose/core/__init__.py`
- [x] Create `goose/core/app.py` - `GooseApp` class
- [x] Create `goose/core/loader.py` - load app from `module:var` path
- [x] Move reload logic to `goose/core/reload.py`
- [x] Move WebSocket manager to `goose/core/websocket.py`
- [x] Add tests: `tests/core/test_app.py` - GooseApp instantiation
- [x] Add tests: `tests/core/test_loader.py` - load_app, get_effective_reload_targets

**Files**:
```
goose/core/
├── __init__.py
├── app.py          # GooseApp class
├── loader.py       # load_app(), get_app(), get_effective_reload_targets()
├── reload.py       # Module reload logic (move from api/)
└── websocket.py    # ConnectionManager (move from api/)

tests/core/
├── test_app.py
└── test_loader.py
```

**Exit Criteria**: `make test` passes, GooseApp works

---

### Phase 2: Consolidate CLI ✅
**Goal**: Single `goose` command with subcommands

- [x] Refactor `goose/cli.py` to be main Typer app
- [x] Move API server logic to `goose api` subcommand
- [x] Move test runner logic to `goose test run` subcommand
- [x] Create `goose/testing/cli.py` for testing subcommands
- [x] Add `goose init` command (creates `gooseapp/` folder)
- [x] Update `pyproject.toml` to single entry point
- [x] Add tests: `tests/test_cli.py` - test subcommand structure, init command

**Commands**:
```bash
goose init                          # Create gooseapp/ folder
goose api --app gooseapp.app:app    # Start dashboard
goose test run gooseapp.tests       # Run tests CLI
goose test list gooseapp.tests      # List tests
```

**Exit Criteria**: `make test` passes, all CLI commands work

---

### Phase 3: Update API to use GooseApp ✅
**Goal**: API accepts `--app` and loads `GooseApp`

- [x] Update `goose api` command to accept `--app module:var`
- [x] Update `goose/api/app.py` to receive `GooseApp` instance
- [x] Update hot reload to use `get_effective_reload_targets()`
- [x] Ensure `gooseapp` is always in reload targets
- [x] Update state management to re-fetch app after reload
- [x] Update existing API tests to use new pattern
- [x] Add tests: hot reload includes gooseapp module

**Exit Criteria**: `make test` passes, API starts with `--app`

---

### Phase 4: Add Route Prefixes ✅
**Goal**: All routes under `/testing/*`

- [x] Create `goose/testing/api/router.py` with prefixed routes
- [x] Move routes from `goose/api/routes.py` to testing router
- [x] Mount testing router at `/testing` prefix
- [x] Update frontend API client to use `/testing/*` paths
- [x] Keep `/health` and `/ws` at root
- [x] Update all route tests to use `/testing/*` prefix

**Routes**:
```
GET  /testing/tests
GET  /testing/runs
POST /testing/runs
GET  /testing/runs/{id}
GET  /health
WS   /ws
```

**Exit Criteria**: `make test` passes, frontend works with new routes

---

### Phase 5: Create Tooling Module ✅
**Goal**: Backend for tool browsing and invocation

- [x] Create `goose/tooling/__init__.py`
- [x] Create `goose/tooling/executor.py` - invoke tools (sync + async)
- [x] Create `goose/tooling/schema.py` - extract tool schema from LangChain tools
- [x] Create `goose/tooling/api/__init__.py`
- [x] Create `goose/tooling/api/router.py` - `/tooling/*` routes
- [x] Create `goose/tooling/api/schema.py` - Pydantic models for API
- [x] Mount tooling router in main app
- [x] Add tests: `tests/tooling/test_executor.py` - sync/async tool invocation
- [x] Add tests: `tests/tooling/test_schema.py` - schema extraction from @tool
- [x] Add tests: `tests/tooling/test_routes.py` - API endpoints

**Routes**:
```
GET  /tooling/tools              # List tools with schema
GET  /tooling/tools/{name}       # Tool details
POST /tooling/tools/{name}/invoke  # Execute tool
```

**Exit Criteria**: `make test` passes, can invoke tools via API

---

### Phase 6: Frontend - Tab Navigation ✅
**Goal**: Add tabs to switch between Testing and Tooling views

- [x] Refactor `App.tsx` - extract current dashboard to `TestingView.tsx`
- [x] Add tab navigation component in `App.tsx`
- [x] Add routing (`/testing`, `/tooling`)
- [x] Create `views/TestingView.tsx` (move existing code)
- [x] Create placeholder `views/ToolingView.tsx`
- [x] Update API client structure (`api/testing.ts`, `api/tooling.ts`)

**Exit Criteria**: `make test` passes, can switch tabs, Testing view works

---

### Phase 7: Frontend - Tooling View ✅
**Goal**: UI for browsing and invoking tools

- [x] Create `views/ToolingView.tsx` - main layout
- [x] Create `components/tooling/ToolList.tsx` - list of tools
- [x] Create `components/tooling/ToolCard.tsx` - tool summary card
- [x] Create `components/tooling/ToolDetail.tsx` - tool details + invoke form
- [x] Create `components/tooling/InvokeForm.tsx` - form from JSON schema
- [x] Create `components/tooling/InvokeResult.tsx` - display result/error
- [x] Add API calls in `api/tooling.ts`

**Exit Criteria**: `make test` passes, can browse and invoke tools in UI

---

### Phase 8: Update Example Project ✅
**Goal**: Migrate example to new structure

- [x] Create `gooseapp/` folder in project root
- [x] Create `gooseapp/app.py` with `GooseApp`
- [x] Move `example_tests/` to `gooseapp/tests/`
- [x] Update `gooseapp/conftest.py` (at package root for discovery)
- [x] Keep old `example_tests/` for backward compatibility
- [x] Update README with new structure
- [x] Verify CLI discovers tests from gooseapp.tests

**Exit Criteria**: `make test` passes, example works with new structure

---

### Phase 9: Cleanup & Polish ✅
**Goal**: Remove old code, update docs

- [x] Keep legacy CLI entry points in `pyproject.toml` (marked deprecated)
- [x] Keep `goose/api/cli.py` for backward compatibility
- [x] Update README.md with:
  - [x] New project structure (`gooseapp/`)
  - [x] New CLI commands (`goose init`, `goose api`, `goose test`)
  - [x] GooseApp configuration documentation
- [x] Update ARCHITECTURE.md - mark all phases complete
- [x] Final test run - 118 tests passing

**Exit Criteria**: `make test` passes, clean codebase, README fully updated

---

## Checkpoints

After each phase:
1. Run `make test` - all tests must pass
2. Manual smoke test of affected functionality
3. Commit with descriptive message
