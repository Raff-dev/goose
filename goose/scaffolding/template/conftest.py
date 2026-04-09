"""Goose test fixtures.

This module defines the fixture that provides a Goose instance to your tests.
The fixture wires up your agent's query function and validator model.

The @fixture decorator registers your fixture with Goose's discovery system.
Fixtures are injected into test functions by matching parameter names.

Example:
    from goose.testing import Goose, fixture
    from my_agent import query_my_agent

    @fixture()
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
# Your query function should have this contract:
#
#     from goose.testing.models.messages import AgentResponse, Message
#
#     def query(message: str) -> AgentResponse:
#         result = run_my_agent(message)
#         return AgentResponse(
#             messages=[
#                 Message(type="ai", content=result.text),
#             ]
#         )
#
# Goose passes the exact `query=` string from goose.case(...) into this
# function. Return at least one final AI message. If you already use
# LangChain responses, normalize them with AgentResponse.from_langchain(...).
# See goose.testing.models.messages.AgentResponse for the full shape,
# including tool call support for expected_tool_calls=[...].
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
    # TODO: Replace with your agent's query function.
    # See https://github.com/Raff-dev/goose/blob/main/docs/getting-started.md
    # for the canonical query -> fixture -> test setup flow.
    # return Goose(
    #     agent_query_func=query_my_agent,
    #     validator_model="gpt-4o-mini",
    # )
    raise NotImplementedError("Configure goose fixture in conftest.py with your agent's query function")
