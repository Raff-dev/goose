"""CLI entrypoints for the Goose agent."""

import sys

import typer
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from gooseapp.conftest import query

app = typer.Typer()


@app.command()
def chat() -> None:
    """Start an interactive chat session with the Goose Outfitters assistant."""
    typer.echo("Welcome to Goose Outfitters Assistant! Type 'exit' to quit.")
    typer.echo("Ask questions about our store, products, sales, and promotions.\n")

    history: list[BaseMessage] = []

    while True:
        try:
            user_input = typer.prompt("You")
            if user_input.lower().strip() in ("exit", "quit", "q"):
                typer.echo("Goodbye!")
                break

            typer.echo("Assistant: ", nl=False)
            response = query(user_input, history)

            content = response["messages"][-1].content
            typer.echo(content)
            typer.echo(response)

            # Update history for context
            history.append(HumanMessage(content=user_input))
            history.append(AIMessage(content=content))

        except KeyboardInterrupt:
            typer.echo("\nGoodbye!")
            break
        except EOFError:
            typer.echo("\nGoodbye!")
            break


@app.command()
def ask() -> None:
    """Query the Goose Outfitters assistant with a single message and print the response."""
    if len(sys.argv) < 2:
        typer.echo("Error: Please provide a message to query", err=True)
        sys.exit(1)

    message = " ".join(sys.argv[1:])
    response = query(message)
    content = response["messages"][-1].content
    typer.echo(content)


@app.command()
def placeholder() -> None:
    """Placeholder command."""
