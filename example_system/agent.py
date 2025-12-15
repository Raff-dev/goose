"""Agent building and query functions for the Goose Outfitters system."""

from __future__ import annotations

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import BaseMessage, HumanMessage

from example_system.tools import TOOLS
from goose.testing.models.messages import AgentResponse

load_dotenv()

SYSTEM_PROMPT = """
You are a helpful assistant for Goose Outfitters, a retail store specializing in trail and backcountry gear.

You have access to various tools to help answer questions about the store, products, sales, and operations.
Use the tools when needed to provide accurate information.

When answering questions:
- Be concise but informative
- Use the tools to get current data
- Format numbers appropriately (currency, percentages)
- If multiple tools are needed, use them in sequence"""


# Pre-built agent instance for use with GooseApp
agent = create_agent(
    model="gpt-4o-mini",
    tools=TOOLS,
    system_prompt=SYSTEM_PROMPT,
    name="Goose Outfitters Agent",
)


def query(question: str, history: list[BaseMessage] | None = None) -> AgentResponse:
    """Query the agent with a question.

    Args:
        question: The question to ask the agent.
        history: Optional list of previous conversation messages.

    Returns:
        The agent's response payload.
    """
    messages = (history or []) + [HumanMessage(content=question)]
    result = agent.invoke({"messages": messages})
    return AgentResponse.from_langchain(result)
