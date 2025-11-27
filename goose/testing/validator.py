"""Agent validator for testing LLM agent behavior."""

from __future__ import annotations

from datetime import datetime

from dotenv import load_dotenv  # pylint: disable=import-error
from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from goose.testing.models.messages import AgentResponse

load_dotenv()


class ExpectationsEvaluationResponse(BaseModel):
    """Structured output for agent behavior validation."""

    reasoning: str = Field(description="Detailed reasoning about whether the agent behavior matches expectations")
    unmet_expectation_numbers: list[int] = Field(
        description="List of expectation numbers that were not met",
        default_factory=list,
    )


class AgentValidator:
    """Encapsulated agent validator for testing LLM behavior."""

    def __init__(self, chat_model: BaseChatModel | str) -> None:
        """Build the LangChain validator agent without tools."""
        current_date = datetime.now().strftime("%B %d, %Y")
        self._agent = create_agent(
            model=chat_model,
            tools=[],  # No tools needed for validation
            response_format=ExpectationsEvaluationResponse,
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

    def evaluate(self, agent_output: AgentResponse, expectations: list[str]) -> ExpectationsEvaluationResponse:
        """Validate agent output against expectations.

        Args:
            agent_output: Either the complete output string from the agent's execution,
                         or the raw response dict from agent.query() (will be formatted automatically).
            expectations: List of expectations the agent should have met.

        Returns:
            The validator's assessment as a ExpectationsEvaluationResponse.
        """

        agent_output_str = agent_output.format_for_validation()
        prompt = f"""
AGENT OUTPUT:
{agent_output_str}

EXPECTATIONS:
{chr(10).join(f"{index}. {exp}" for index, exp in enumerate(expectations, start=1))}

Analyze if the agent behavior matches these expectations.
"""

        messages = [HumanMessage(content=prompt)]
        result = self._agent.invoke({"messages": messages})
        return result["structured_response"]


__all__ = ["AgentValidator", "ExpectationsEvaluationResponse"]
