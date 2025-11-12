# Goose Testing Framework PRD (Updated)

## Overview
A Python testing framework for validating LLM agent behavior, tool usage, and side effects. Supports modular test suites with fixtures, repetitions, and custom validations. Agents and setups are many-to-many via multiple Goose instances. Similar to pytest's fixture injection.

## Core Features
- **Goose Instances**: Configurable with agent functions, default attempts, and setup fixtures (e.g., DB initialization). `Goose(agent, attempts=1, setup_func=None)`.
- **Test Functions**: Plain async functions that take a Goose instance (fixture-like injection).
- **Case Creation and Execution**: `case = goose.case()` creates TestCase (runs Goose setup); `await case.run(query, expectations, tool_calls, attempts=N)` executes with params, allowing dynamic expectations.
- **Defaults and Overrides**: Attempts and setup defaults set in Goose, overridable in `run()`.
- **Combining Suites**: `TestRunner(tests, goose)` runs test functions with a Goose instance; supports multiple TestRunners for different combinations.
- **Results and Validations**: Collects pass/fail, reasoning, attempt counts; catches `AssertionError` from post-run asserts for custom validations (e.g., DB checks).

## Requirements
- **Functional**:
  - Create Goose with agent func, default attempts, and optional setup func.
  - Define tests as async functions taking a Goose param.
  - Create cases with `goose.case()`, run with `case.run(query, expectations, tool_calls, attempts)`.
  - Support pre-run setup in test bodies (e.g., add transactions).
  - Use asserts after `case.run()` for custom validations; framework catches failures.
  - Override attempts/setup per run.
  - Combine tests with different Goose instances via TestRunner for integrated testing.
- **User Stories**:
  - As a developer, I want to test agent responses against expectations to ensure correct output.
  - As a developer, I want retries for non-deterministic LLMs to reduce false failures.
  - As a developer, I want custom DB validations for state-changing actions using post-run asserts.
  - As a developer, I want modular suites (e.g., products, transactions) with many-to-many agents/setups that combine for full tests.
  - As a developer, I want dynamic expectations based on pre-run setup.
- **Non-Functional**:
  - Async support for LLM calls.
  - Exception handling for asserts (fail on AssertionError).
  - Simple API, minimal boilerplate; fixture-like injection similar to pytest.
  - Compatible with existing Goose codebase.

## Assumptions
- Users provide async agent query functions.
- Expectations are descriptive strings for LLM validation, can be dynamic.
- Custom validations use Python asserts after run.
- No global state; each Goose is independent with its own defaults.
- Framework integrates with Goose models and AgentValidator.
