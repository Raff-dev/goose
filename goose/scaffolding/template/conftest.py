"""Goose test fixtures.

This module defines the fixture that provides a Goose instance to your tests.
The fixture wires up your agent's query function and validator model.

The @fixture decorator registers your fixture with Goose's discovery system.
Fixtures are injected into test functions by matching parameter names.

Example:
    from goose.testing import Goose, fixture
    from my_agent import query_my_agent

    @fixture
    def goose() -> Goose:
        return Goose(
            agent_query_func=query_my_agent,
            validator_model="gpt-4o-mini",
        )

    # In tests, receive the fixture by parameter name:
    def test_something(goose: Goose) -> None:
        goose.case(...)
"""

from goose.testing import Goose, fixture

# =============================================================================
# Import your agent's query function
# =============================================================================
# Your query function should have this signature:
#
#     def query(message: str) -> AgentResponse:
#         ...
#
# It should invoke your LangChain agent and return an AgentResponse.
# See goose.testing.models.messages.AgentResponse for the expected format.
#
# Example:
#     from my_agent import query_weather_agent

# =============================================================================
# Goose Fixture
# =============================================================================


@fixture()
def goose() -> Goose:
    """Create the Goose test fixture.

    This fixture is injected into test functions that have a `goose` parameter.
    Customize it with your agent's query function.

    Returns:
        Goose: A configured Goose instance for testing.

    Configuration options:
        agent_query_func: Callable that sends a message to your agent and
                          returns an AgentResponse. Required.

        validator_model: The LLM model for validating expectations.
                         Can be a string ("gpt-4o-mini") or a LangChain
                         BaseChatModel instance. Default: "gpt-4o-mini"

        hooks: Optional TestLifecycleHooks instance for setup/teardown.
               See goose.testing.hooks for details.

    Example:
        @fixture()
        def goose() -> Goose:
            return Goose(
                agent_query_func=query_weather_agent,
                validator_model="gpt-4o-mini",
            )
    """
    # TODO: Replace with your agent's query function
    # return Goose(
    #     agent_query_func=query_my_agent,
    #     validator_model="gpt-4o-mini",
    # )
    raise NotImplementedError("Configure goose fixture in conftest.py with your agent's query function")
