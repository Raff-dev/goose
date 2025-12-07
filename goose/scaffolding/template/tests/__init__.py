"""Goose test package.

This package contains your behavioral tests for your LLM agent.
Tests are defined using the @test decorator and use the Goose fixture
for interacting with your agent.

Test discovery:
    - Files must be named test_*.py or *_test.py
    - Test functions must be decorated with @test
    - Tests use the `goose` fixture defined in conftest.py

Running tests:
    goose test run                    # Run all tests
    goose test run gooseapp.tests     # Run tests in this package
    goose test run gooseapp.tests.test_example  # Run specific module
    goose test list                   # List all discovered tests

Dashboard:
    goose api                         # Start the web dashboard
"""
