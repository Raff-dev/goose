# `goose init`

`goose init` scaffolds the fixed `gooseapp/` layout that Goose expects.

```bash
goose init
goose init path/to/project
goose init --force
```

Under the hood, Goose copies `goose/scaffolding/template/` into `<path>/gooseapp` and then prints the next
steps from the CLI:

1. edit `gooseapp/app.py`
2. edit `gooseapp/conftest.py`
3. add tests in `gooseapp/tests/`
4. run `goose test list gooseapp.tests`
5. run `goose test run gooseapp.tests`
6. run `goose api`

## What gets generated

`goose init` creates this starter tree:

```text
gooseapp/
├── README.md
├── __init__.py
├── app.py
├── conftest.py
└── tests/
    ├── __init__.py
    └── test_example.py
```

What each file is for:

- `gooseapp/app.py` - exports `app = GooseApp(...)`, where you register tools, agents, `reload_targets`, and
  `reload_exclude`
- `gooseapp/conftest.py` - registers your Goose fixture with `@fixture()` and wires in the agent query function
- `gooseapp/tests/` - holds `test_*.py` modules and `test_*` functions that Goose discovers
- `gooseapp/README.md` - the scaffold's local reference for test-writing patterns and dashboard usage

`gooseapp/data/` is not part of the scaffold. It appears later when test runs are persisted.

## What Goose expects from the scaffold

`goose api` validates the same fixed structure described in `goose/core/config.py`:

```text
gooseapp/
├── app.py
├── conftest.py
└── tests/
```

More specifically:

- `gooseapp/` must exist
- `gooseapp/app.py` must exist and export `app`
- `gooseapp/tests/` must exist
- the exported `app` must be a valid `GooseApp`

If that structure is broken, `goose api` exits with an error and tells you to run `goose init`.

## Recommended edit order

Follow the order the scaffold CLI prints:

### 1. `gooseapp/app.py`

Start here. Register the surface area Goose should know about:

- `tools=[...]` or `tool_groups={...}` for the Tooling view
- `agents=[...]` for live chat
- `reload_targets=[...]` for source packages you want reloaded
- `reload_exclude=[...]` for packages that should stay untouched during reload

### 2. `gooseapp/conftest.py`

Wire the `goose` fixture to the real agent entrypoint:

```python
@fixture(name="goose")
def goose_fixture() -> Goose:
    return Goose(
        agent_query_func=query,
        validator_model="gpt-4o-mini",
    )
```

That `query` callable receives the exact user message from `goose.case(query=...)` and must return
`AgentResponse`. See [`testing.md`](testing.md) for a concrete example of the contract.

If your app needs setup or teardown, attach lifecycle hooks here too.

### 3. `gooseapp/tests/`

Replace `test_example.py` with real cases. Goose discovers:

- modules named `test_*.py` or `tests_*.py`
- functions named `test_*`

See [`testing.md`](testing.md) for the full authoring guide.

## Next steps after init

Once the scaffold is wired:

```bash
goose test list
goose test run -v
goose api
goose-dashboard
```

- use [`testing.md`](testing.md) to write cases
- use [`running-goose.md`](running-goose.md) to understand the runtime loop
- use [`dashboard.md`](dashboard.md) to debug in the UI

## `--force`

If `gooseapp/` already exists, `goose init` fails by default:

```text
Directory /path/to/gooseapp already exists. Use --force to overwrite.
```

`goose init --force` removes the existing `gooseapp/` directory and recreates it from the template. Use it only
when you intentionally want to replace the scaffold.
