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

    reasoning: str = Field(
        description=(
            "Step-by-step analysis of the agent's behavior. "
            "For EACH numbered expectation, explicitly state whether it was MET or UNMET and why."
        )
    )
    unmet_expectation_numbers: list[int] = Field(
        description=(
            "List of expectation numbers (integers) that were NOT met. "
            "Must be empty list [] if all expectations were met."
        ),
        default_factory=list,
    )
    failure_reasons: dict[int, str] = Field(
        description=(
            "REQUIRED for each unmet expectation. "
            "Map of expectation number -> concise failure explanation. "
            "Example: {1: 'Agent listed products instead of creating one', 3: 'No email was sent'}"
        ),
        default_factory=dict,
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
            system_prompt=f"""You are an expert validator for LLM agent behavior testing.

Current date: {current_date}

TASK: Analyze agent execution output against numbered expectations and determine which expectations were met or unmet.

INSTRUCTIONS:
1. Read the agent output carefully - look at tool calls made and their results
2. For EACH numbered expectation, determine if it was MET or UNMET
3. In your reasoning, explicitly address each expectation by number

CRITICAL REQUIREMENTS:
- If an expectation is UNMET, you MUST add its number to unmet_expectation_numbers
- For EVERY unmet expectation number, you MUST provide a failure_reason entry explaining what went wrong
- The failure_reasons dict MUST have an entry for each number in unmet_expectation_numbers
- Failure reasons should be specific: "Agent called X instead of Y" or "No tool call for Z was made"

EXAMPLE OUTPUT FORMAT:
- reasoning: "1. MET - Agent called create_product with correct params. 2. UNMET - Agent did not send confirmation email. 3. MET - Price was set to $50."
- unmet_expectation_numbers: [2]
- failure_reasons: {{2: "No send_email tool call was made after product creation"}}""",
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
        prompt = f"""AGENT OUTPUT:
{agent_output_str}

EXPECTATIONS TO VALIDATE:
{chr(10).join(f"{index}. {exp}" for index, exp in enumerate(expectations, start=1))}

Analyze the agent's behavior against each numbered expectation.
For each expectation, state if it was MET or UNMET.
If UNMET, include the number in unmet_expectation_numbers AND provide a specific failure_reason."""

        messages = [HumanMessage(content=prompt)]
        result = self._agent.invoke({"messages": messages})
        return result["structured_response"]


__all__ = ["AgentValidator", "ExpectationsEvaluationResponse"]
