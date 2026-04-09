# Running Goose

Goose has a simple runtime loop:

1. the Python API serves testing, tooling, and chat backends
2. the dashboard serves the browser UI
3. tests can run either from the CLI or through the Testing view

The config that drives this lives in two places:

- `gooseapp/app.py` - tools, chat agents, `reload_targets`, `reload_exclude`
- `gooseapp/conftest.py` - the Goose fixture and your `query(...) -> AgentResponse` adapter

## 1. Start the API

```bash
goose api
```

By default this starts on `127.0.0.1:8730`.

`goose api` does three important things before serving:

- validates the fixed `gooseapp/` structure
- loads `gooseapp.app:app`
- computes reload targets from `GooseApp.reload_targets` plus `gooseapp`

On startup it prints:

```text
Starting Goose dashboard
  Tests: gooseapp.tests
  Reload targets: [...]
```

You can bind a different host or port:

```bash
goose api --host 0.0.0.0 --port 9000
```

## 2. Start the dashboard

In a second terminal:

```bash
goose-dashboard
```

The dashboard CLI serves the web app on `http://localhost:8729/`.

By default it talks to the Goose API at `http://localhost:8730`. If your API is elsewhere, point the dashboard at
it with either:

```bash
goose-dashboard --api-url http://localhost:9000
```

or:

```bash
GOOSE_API_URL=http://localhost:9000 goose-dashboard
```

The CLI logs the API URL when `GOOSE_API_URL` is set.

## What runs where

### Browser routes

The dashboard routes are:

- `/testing`
- `/tooling`
- `/chat`

### API routes

The FastAPI backend mounts:

- `/testing`
- `/tooling`
- `/chatting`

So the mental model is still **Testing / Tooling / Chatting**, even though the browser tab URL is currently
`/chat`.

## What to expect in each surface

- **Testing** - discover tests, run them, inspect results and traces
- **Tooling** - invoke registered tools directly without running the whole agent
- **Chatting** - create conversations against configured agents and watch live tool activity

If you only need a first passing test, you can stop at `goose test list` / `goose test run` and leave the browser loop
for later.

The browser is just the UI. The Python side does the real work:

- test discovery and execution
- tool invocation
- conversation APIs and WebSocket streaming
- GooseApp loading and validation

## Hot reload: `reload_targets` and `reload_exclude`

There are two reload ideas to keep in mind.

### Server reload

`goose api` starts uvicorn with `reload=True`, so backend code changes restart the API process during development.

### Source reload before tests

Before Goose discovers or runs tests, it reloads source modules and then re-imports `gooseapp.conftest`.

That reload set comes from:

- `gooseapp` - always included
- anything you add in `GooseApp(reload_targets=[...])`

Modules matching `reload_exclude=[...]` are skipped during that source reload pass.

The example app shows the intended shape:

```python
app = GooseApp(
    tool_groups={...},
    reload_targets=["example_system"],
    reload_exclude=["example_system.models"],
    agents=[agent],
)
```

Use `reload_targets` for the packages you edit often. Use `reload_exclude` for modules that should stay stable
during reload, such as Django models or expensive initialization points.

## When `gooseapp/` is invalid

`goose api` validates the scaffold before serving. If the structure is wrong, it exits with code `1`.

Common failures:

- `Directory not found: .../gooseapp`
- `Missing app file: .../gooseapp/app.py`
- `Missing tests directory: .../gooseapp/tests`
- `Error loading gooseapp/app.py: ...`

The last case covers import errors, a missing exported `app`, or invalid `GooseApp` configuration.

## CLI test loop

You do not need the dashboard to run tests:

```bash
goose test list
goose test run
goose test run -v gooseapp.tests
```

`goose test` uses the same discovery rules and writes run data under `gooseapp/data/`.

If you want to understand the UI side of the same loop, continue with [`dashboard.md`](dashboard.md).
