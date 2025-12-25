"""Agent building for the Goose Outfitters system."""

from __future__ import annotations

from dotenv import load_dotenv
from langchain.agents import create_agent

from example_system.tools import TOOLS

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
