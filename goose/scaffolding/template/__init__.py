"""Goose application package.

This package contains your Goose application configuration, test fixtures,
and test files. The structure follows the Goose convention:

    gooseapp/
    ├── __init__.py     # This file - package marker
    ├── app.py          # GooseApp configuration (tools, reload targets)
    ├── conftest.py     # Test fixtures (goose fixture for agent testing)
    └── tests/          # Your test files
        ├── __init__.py
        └── test_*.py   # Test modules with @test decorated functions

Key concepts:
    - GooseApp: Central configuration for your agent's tools and hot-reload
    - Fixtures: Provide the Goose test runner with your agent's query function
    - Tests: Define behavioral expectations for your LLM agent

Run `goose api` to start the dashboard, or `goose test run` for CLI testing.
"""
