"""Goose test package.

This package contains your behavioral tests for your LLM agent.
Tests are ordinary `test_*` functions that use the Goose fixture to
interact with your agent.

Test discovery:
    - Files must be named test_*.py or tests_*.py
    - Test functions must be named test_*
    - Tests use the `goose` fixture defined in conftest.py

Running tests:
    goose test run                    # Run all tests
    goose test run gooseapp.tests     # Run tests in this package
    goose test run gooseapp.tests.test_example  # Run specific module
    goose test list                   # List all discovered tests

Development loop:
    goose api                         # Start the Goose backend API
    goose-dashboard                   # Start the dashboard UI
"""
