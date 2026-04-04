# Goose app local guide

This `gooseapp/` package is your local Goose workspace.

## What to edit first

- `app.py` - register the tools and agents Goose should expose, plus any `reload_targets`
- `conftest.py` - wire the `goose` fixture to your real agent query function
- `tests/` - keep your Goose cases here; start by replacing `test_example.py`

## First run

Run these from the project root after you wire `app.py` and `conftest.py`:

```bash
goose test list gooseapp.tests
goose test run gooseapp.tests
goose api
goose-dashboard
```

Use them in this order:

1. `goose test list gooseapp.tests` - confirm Goose discovers your test package
2. `goose test run gooseapp.tests` - run your cases from the CLI
3. `goose api` - start the Goose backend API for testing, tooling, and chat
4. `goose-dashboard` - open the dashboard UI in a second terminal

## Canonical docs

For the full workflow, use the main Goose docs:

- init flow: <https://github.com/Raff-dev/goose/blob/main/docs/goose-init.md>
- writing tests: <https://github.com/Raff-dev/goose/blob/main/docs/testing.md>
- running the backend and CLI loop: <https://github.com/Raff-dev/goose/blob/main/docs/running-goose.md>
- using the dashboard: <https://github.com/Raff-dev/goose/blob/main/docs/dashboard.md>
