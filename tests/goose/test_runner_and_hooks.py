from __future__ import annotations

from unittest import mock

from goose.testing.engine import Goose
from goose.testing.hooks import TestLifecycleHooks
from goose.testing.models.tests import TestDefinition, TestResult
from goose.testing.runner import execute_test


def _definition() -> TestDefinition:
    def sample(goose: Goose):
        goose.case(query="hi", expectations=["Responded"], expected_tool_calls=None)

    return TestDefinition(module="pkg.tests", name="test_sample", func=sample)


class DummyHooks(TestLifecycleHooks):
    def __init__(self) -> None:
        super().__init__()
        self.pre_called = False
        self.post_called = False

    def pre_test(self, definition: TestDefinition) -> None:  # pylint: disable=unused-argument
        self.pre_called = True

    def post_test(self, definition: TestDefinition) -> None:  # pylint: disable=unused-argument
        self.post_called = True


def test_execute_test_runs_hooks_and_returns_result(monkeypatch):
    hooks = DummyHooks()

    class DummyGoose(Goose):
        def __init__(self):
            super().__init__(agent_query_func=lambda query: mock.Mock(tool_call_names=[]), hooks=hooks)

        def case(self, *args, **kwargs):  # type: ignore[override]
            self._test_case = mock.Mock(last_response=mock.Mock(tool_call_names=[]))

    goose_instance = DummyGoose()

    def fake_build_call_arguments(func, cache):  # pylint: disable=unused-argument
        return {"goose": goose_instance}

    def fake_extract(cache):  # pylint: disable=unused-argument
        return goose_instance

    monkeypatch.setattr("goose.testing.runner.build_call_arguments", fake_build_call_arguments)
    monkeypatch.setattr("goose.testing.runner.extract_goose_fixture", fake_extract)
    monkeypatch.setattr("goose.testing.runner.apply_autouse", lambda cache: None)

    definition = _definition()
    result = execute_test(definition)

    assert isinstance(result, TestResult)
    assert hooks.pre_called and hooks.post_called


def test_execute_test_captures_exceptions(monkeypatch):
    def failing_test():
        raise RuntimeError("boom")

    definition = TestDefinition(module="pkg.tests", name="test_fail", func=lambda: failing_test())

    monkeypatch.setattr("goose.testing.runner.build_call_arguments", lambda func, cache: {})
    monkeypatch.setattr(
        "goose.testing.runner.extract_goose_fixture",
        lambda cache: mock.Mock(hooks=TestLifecycleHooks(), consume_test_case=lambda: None),
    )
    monkeypatch.setattr("goose.testing.runner.apply_autouse", lambda cache: None)

    result = execute_test(definition)

    assert result.exception is not None
    assert result.error_type is not None
