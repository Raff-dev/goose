"""Agent building and query functions for the Goose Outfitters system."""

from __future__ import annotations

from typing import Any

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

DEFAULT_MODEL = "gpt-4o-mini"


def get_agent(model: str = DEFAULT_MODEL) -> Any:
    """Build an agent with the specified model.

    This factory function is used by both the chatting module and
    other callers to create agents.

    Args:
        model: The model name to use (e.g., "gpt-4o-mini", "gpt-4o").

    Returns:
        A LangChain agent configured with the specified model.
    """
    return create_agent(
        model=model,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )


def query(question: str, history: list[BaseMessage] | None = None, model: str = DEFAULT_MODEL) -> AgentResponse:
    """Query the agent with a question.

    Args:
        question: The question to ask the agent.
        history: Optional list of previous conversation messages.
        model: The model to use for the query.

    Returns:
        The agent's response payload.
    """
    agent = get_agent(model)
    messages = (history or []) + [HumanMessage(content=question)]
    result = agent.invoke({"messages": messages})
    return AgentResponse.from_langchain(result)
