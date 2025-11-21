"""Agent validator for testing LLM agent behavior."""

from __future__ import annotations

from datetime import datetime

from dotenv import load_dotenv  # pylint: disable=import-error
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from goose.testing.models import AgentResponse

load_dotenv()


class ValidationResponse(BaseModel):
    """Structured output for agent behavior validation."""

    reasoning: str = Field(description="Detailed reasoning about whether the agent behavior matches expectations")
    unmet_expectation_numbers: list[int] = Field(
        description="List of expectation numbers that were not met",
        default_factory=list,
    )
    error: bool = Field(description="True if the agent behavior does NOT match expectations, False if it does")


class AgentValidator:
    """Encapsulated agent validator for testing LLM behavior."""

    def __init__(self) -> None:
        self.agent = self._build_agent()

    def _build_agent(self):
        """Build the LangChain validator agent without tools.

        Returns:
            The configured LangChain validator agent.
        """

        current_date = datetime.now().strftime("%B %d, %Y")
        agent = create_agent(
            model="gpt-4o-mini",
            tools=[],  # No tools needed for validation
            response_format=ValidationResponse,
            system_prompt=f"""
You are an expert validator for LLM agent behavior testing.

Current date: {current_date}

You will be given:
1. The complete output from an agent's execution (tool calls and responses)
2. A list of expectations that describe what the agent should have done

Your task is to analyze whether the agent's behavior matches these expectations and provide a structured assessment.

When validating:
- Be thorough but concise in your analysis
- Clearly state whether expectations are met
- Provide specific reasoning for your assessment
- Focus on the agent's actual behavior vs expected behavior
- Each expectation will be numbered. Use these numbers when referring to expectations.
- If any expectations are not met, include their numbers in unmet_expectation_numbers and
    reference those numbers in your reasoning""",
        )
        return agent

    def validate(self, agent_output, expectations: list[str]) -> ValidationResponse:
        """Validate agent output against expectations.

        Args:
            agent_output: Either the complete output string from the agent's execution,
                         or the raw response dict from agent.query() (will be formatted automatically).
            expectations: List of expectations the agent should have met.

        Returns:
            The validator's assessment as a ValidationResponse.
        """
        # Handle different input types
        if isinstance(agent_output, dict):
            # Convert raw response dict to AgentResponse and format
            response_obj = AgentResponse.from_dict(agent_output)
            agent_output = response_obj.format_for_validation()
        elif isinstance(agent_output, AgentResponse):
            # Already structured, format for validation
            agent_output = agent_output.format_for_validation()

        prompt = f"""
AGENT OUTPUT:
{agent_output}

EXPECTATIONS:
{chr(10).join(f"{index}. {exp}" for index, exp in enumerate(expectations, start=1))}

Analyze if the agent behavior matches these expectations.
"""

        messages = [HumanMessage(content=prompt)]
        result = self.agent.invoke({"messages": messages})
        return result["structured_response"]


__all__ = ["AgentValidator", "ValidationResponse"]
