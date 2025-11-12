"""Testing framework for validating agent behavior and tool usage."""

from __future__ import annotations

import asyncio
import importlib
import inspect
import os
import sys
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_core.tools import BaseTool

from goose.agent_validator import AgentValidator, ValidationResult
from goose.models import AgentResponse


@dataclass(slots=True)
class RetryConfig:
    """Configuration for retrying flaky agent validations."""

    attempts: int = 1
    sleep_between_attempts: float = 0.0


class TestCase:
    """Represents a single test case for agent behavior validation."""

    def __init__(
        self,
        query: str,
        expectations: list[str],
        *,
        goose: Goose,
        expected_tool_calls: list[BaseTool] | None = None,
        retry: RetryConfig | None = None,
    ):  # pylint: disable=too-many-arguments
        self.query = query
        self.expectations = expectations
        self.expected_tool_calls = expected_tool_calls
        self.goose = goose
        retry_config = retry or RetryConfig()
        # Number of times to attempt running this test case (helpful for flaky LLM responses)
        self.attempts = max(1, int(retry_config.attempts))
        # Optional sleep (in seconds) between attempts
        self.sleep_between_attempts = float(retry_config.sleep_between_attempts)
        self._result: ValidationResult | None = None

    def validate_tool_calls(self, response: AgentResponse) -> ValidationResult:
        """Validate that the agent response contains the expected tool calls.

        Args:
            response: The parsed agent response to validate.

        Returns:
            ValidationResult indicating success or failure with reasoning.
        """
        if self.expected_tool_calls is None:
            return ValidationResult(success=True)

        actual_tool_calls = response.tool_call_names
        expected_tool_names = {tool.name for tool in self.expected_tool_calls}
        actual_tool_names = set(actual_tool_calls)

        if actual_tool_names != expected_tool_names or len(actual_tool_calls) != len(self.expected_tool_calls):
            return ValidationResult(
                success=False,
                reasoning=(f"Tool call mismatch. Expected {sorted(expected_tool_names)}, got {actual_tool_calls}"),
            )

        return ValidationResult(success=True)

    async def is_valid(self) -> bool:
        """Check if the test case passes validation.

        Returns:
            True if the test case passes, False otherwise.
        """
        if self._result is None:
            self._result = await self.goose.run(self)
        return self._result.success

    async def report(self) -> str:
        """Get the validation report for the test case.

        Returns:
            A string describing the test result and reasoning.
        """
        if self._result is None:
            self._result = await self.goose.run(self)
        return self._result.reasoning or ""


class Goose:
    """Testing framework for validating agent behavior and tool calls."""

    def __init__(self, agent_query_func: Callable[[str], dict[str, Any]]):
        self._agent_query_func = agent_query_func
        self._validation_agent = AgentValidator()

    async def run(self, test_case: TestCase) -> ValidationResult:
        """Execute a test case and validate the agent response.

        Args:
            test_case: The test case to execute.

        Returns:
            ValidationResult indicating success or failure with reasoning and timing.
        """
        last_reason: str | None = None
        for attempt in range(1, test_case.attempts + 1):
            start_time = time.time()
            raw_response = await asyncio.to_thread(self._agent_query_func, test_case.query)
            execution_time = time.time() - start_time

            # Parse the response using Pydantic
            response = AgentResponse.from_dict(raw_response)

            # Validate expectations
            evaluation = await asyncio.to_thread(self._validation_agent.validate, response, test_case.expectations)
            if evaluation.error:
                last_reason = evaluation.reasoning
            else:
                # Validate tool calls
                tool_call_validation = test_case.validate_tool_calls(response)
                if not tool_call_validation.success:
                    last_reason = tool_call_validation.reasoning
                else:
                    return ValidationResult(
                        success=True,
                        reasoning=f"Test passed in {execution_time:.2f}s on attempt {attempt}/{test_case.attempts}",
                    )

            # If we will retry, optionally sleep before next attempt
            if attempt < test_case.attempts and test_case.sleep_between_attempts > 0:
                time.sleep(test_case.sleep_between_attempts)

        # If we exhausted attempts, report failure with the last reasoning collected
        reason = last_reason or "Test failed after all attempts"
        return ValidationResult(success=False, reasoning=f"{reason} (after {test_case.attempts} attempts)")

    def case(
        self,
        query: str,
        expectations: list[str],
        *,
        expected_tool_calls: list[BaseTool] | None = None,
        retry: RetryConfig | None = None,
    ) -> TestCase:
        """Create a test case for validating agent behavior.

        Args:
            query: The query string to send to the agent.
            expectations: List of expected behaviors or outcomes.
            expected_tool_calls: Optional expected tool call sequence.
            retry: Optional retry configuration overriding defaults.

        Returns:
            A TestCase instance configured with the provided parameters.
        """
        return TestCase(
            query=query,
            expectations=expectations,
            goose=self,
            expected_tool_calls=expected_tool_calls,
            retry=retry,
        )

    def execute(self, test_case: TestCase) -> ValidationResult:
        """Synchronously execute a test case."""

        return asyncio.run(self.run(test_case))

    def assert_case(self, test_case: TestCase) -> ValidationResult:
        """Run a test case and raise AssertionError when it fails."""

        result = self.execute(test_case)
        if not result.success:
            raise AssertionError(result.reasoning or "Goose validation failed")
        return result


@dataclass(slots=True)
class FixtureDefinition:
    """Represents a registered test fixture."""

    func: Callable[..., Any]
    autouse: bool = False


class FixtureRegistry:
    """Simple fixture container inspired by pytest's approach."""

    def __init__(self) -> None:
        self._fixtures: dict[str, FixtureDefinition] = {}

    def register(self, name: str, func: Callable[..., Any], *, autouse: bool = False) -> None:
        if name in self._fixtures:
            raise ValueError(f"Fixture '{name}' already registered")
        self._fixtures[name] = FixtureDefinition(func=func, autouse=autouse)

    def resolve(self, name: str, cache: dict[str, Any]) -> Any:
        definition = self._fixtures.get(name)
        if definition is None:
            raise KeyError(f"Unknown fixture '{name}'")

        cached = cache.get(name, _MISSING)
        if cached is not _MISSING:
            return cached
        if cached is _RESOLVING:
            raise RuntimeError(f"Circular fixture dependency detected for '{name}'")

        cache[name] = _RESOLVING
        try:
            value = self._invoke(definition.func, cache)
        except Exception:  # pragma: no cover - propagate after cleanup
            cache.pop(name, None)
            raise
        cache[name] = value
        return value

    def apply_autouse(self, cache: dict[str, Any]) -> None:
        for name, definition in self._fixtures.items():
            if definition.autouse:
                self.resolve(name, cache)

    def _invoke(self, func: Callable[..., Any], cache: dict[str, Any]) -> Any:
        parameters = inspect.signature(func).parameters
        kwargs = {param: self.resolve(param, cache) for param in parameters}

        if inspect.iscoroutinefunction(func):
            return asyncio.run(func(**kwargs))

        result = func(**kwargs)
        if inspect.iscoroutine(result):
            return asyncio.run(result)
        return result


_MISSING = object()
_RESOLVING = object()
FIXTURE_REGISTRY = FixtureRegistry()


def fixture(*, name: str | None = None, autouse: bool = False):
    """Decorator for registering fixtures with the Goose test runner."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        fixture_name = name or func.__name__
        FIXTURE_REGISTRY.register(fixture_name, func, autouse=autouse)
        return func

    return decorator


@dataclass(slots=True)
class TestDefinition:
    """Metadata describing a registered test function."""

    module: str
    name: str
    func: Callable[..., Any]

    @property
    def qualified_name(self) -> str:
        return f"{self.module}.{self.name}"


@dataclass(slots=True)
class TestResult:
    """Outcome from executing a registered test."""

    definition: TestDefinition
    passed: bool
    duration: float
    error: str | None = None

    @property
    def name(self) -> str:
        return self.definition.qualified_name


TEST_REGISTRY: dict[str, TestDefinition] = {}


def goose_test(func: Callable[..., Any] | None = None, *, name: str | None = None):
    """Decorator to register Goose framework tests."""

    def decorator(target: Callable[..., Any]) -> Callable[..., Any]:
        test_name = name or target.__name__
        definition = TestDefinition(module=target.__module__, name=test_name, func=target)
        TEST_REGISTRY[definition.qualified_name] = definition
        return target

    if func is not None:
        return decorator(func)
    return decorator


def get_registered_tests() -> list[TestDefinition]:
    """Return registered tests ordered by their qualified name."""

    return [TEST_REGISTRY[key] for key in sorted(TEST_REGISTRY)]


def ensure_django_ready(settings_module: str = "example_system.settings") -> None:
    """Ensure Django is configured if available.

    This is a no-op when Django or the example system are not installed.
    """

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
    try:
        import example_system  # noqa: F401  # pylint: disable=unused-import
        return
    except ImportError:
        pass

    try:
        import django
        from django.apps import apps
    except ImportError:  # pragma: no cover - Django not installed
        return

    if not apps.ready:
        django.setup()


def discover_tests(start_dir: str | Path = "example_tests") -> None:
    """Import test modules beneath *start_dir* and register decorated tests."""

    base_path = Path(start_dir)
    if not base_path.exists():
        return

    project_root = Path.cwd().resolve()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    modules = [path for path in base_path.rglob("*.py") if not path.name.startswith("__")]
    modules.sort(key=_module_sort_key)

    for module_path in modules:
        resolved = module_path.resolve()
        if project_root not in resolved.parents and resolved != project_root:
            continue
        module_name = ".".join(resolved.with_suffix("").relative_to(project_root).parts)
        if module_name in sys.modules:
            continue
        importlib.import_module(module_name)


def list_tests(start_dir: str | Path = "example_tests") -> list[TestDefinition]:
    """Return definitions for tests discovered under *start_dir*."""

    ensure_django_ready()
    discover_tests(start_dir)
    return get_registered_tests()


def run_tests(start_dir: str | Path = "example_tests") -> list[TestResult]:
    """Discover and execute tests contained within *start_dir*."""

    ensure_django_ready()
    db_state, django_active = _prepare_test_environment(setup_database=True)
    try:
        discover_tests(start_dir)
        return [_execute_test(definition) for definition in get_registered_tests()]
    finally:
        _teardown_test_environment(db_state, django_active)


def _module_sort_key(path: Path) -> tuple[int, str]:
    name = path.name.lower()
    priority = 0 if ("fixture" in name or "conftest" in name) else 1
    return (priority, str(path))


def _prepare_test_environment(*, setup_database: bool) -> tuple[Any | None, bool]:
    try:
        import django
        from django.test.utils import setup_databases, setup_test_environment  # type: ignore[attr-defined]
    except ImportError:  # pragma: no cover - Django not installed
        return None, False

    setup_test_environment()
    if setup_database:
        db_state = setup_databases(verbosity=0, interactive=False, keepdb=True)
    else:
        db_state = None
    return db_state, True


def _teardown_test_environment(db_state: Any | None, active: bool) -> None:
    if not active:
        return

    from django.test.utils import teardown_databases, teardown_test_environment  # type: ignore[attr-defined]

    if db_state is not None:
        teardown_databases(db_state, verbosity=0)
    teardown_test_environment()


def _execute_test(definition: TestDefinition) -> TestResult:
    start = time.time()
    fixture_cache: dict[str, Any] = {}

    try:
        FIXTURE_REGISTRY.apply_autouse(fixture_cache)
        kwargs = {
            param: FIXTURE_REGISTRY.resolve(param, fixture_cache)
            for param in inspect.signature(definition.func).parameters
        }
        outcome = definition.func(**kwargs)
        _process_test_outcome(outcome, fixture_cache)
    except AssertionError as exc:
        duration = time.time() - start
        message = str(exc) or repr(exc)
        return TestResult(definition=definition, passed=False, duration=duration, error=message)
    except Exception:  # pragma: no cover - unexpected failure path
        duration = time.time() - start
        return TestResult(definition=definition, passed=False, duration=duration, error=traceback.format_exc())

    duration = time.time() - start
    return TestResult(definition=definition, passed=True, duration=duration)


def _process_test_outcome(outcome: Any, fixture_cache: dict[str, Any]) -> None:
    if outcome is None:
        return

    cases: list[TestCase]
    if isinstance(outcome, TestCase):
        cases = [outcome]
    elif isinstance(outcome, (list, tuple)) and all(isinstance(item, TestCase) for item in outcome):
        cases = list(outcome)
    else:
        return

    goose_instance = _extract_goose_fixture(fixture_cache)
    if goose_instance is None:
        raise AssertionError("No Goose fixture available to execute TestCase instances.")

    for case in cases:
        goose_instance.assert_case(case)


def _extract_goose_fixture(cache: dict[str, Any]) -> Goose | None:
    for candidate in ("goose", "goose_fixture"):
        value = cache.get(candidate)
        if isinstance(value, Goose):
            return value
    return None


__all__ = [
    "RetryConfig",
    "TestCase",
    "Goose",
    "ValidationResult",
    "fixture",
    "goose_test",
    "list_tests",
    "run_tests",
    "get_registered_tests",
    "TestResult",
    "TestDefinition",
]
