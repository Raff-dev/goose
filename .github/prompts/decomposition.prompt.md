---
mode: agent
---

# Decomposition of Goose Testing Framework

## Architectural Design Process

The Goose Testing Framework is a complex system designed to validate LLM agent behavior, tool usage, and side effects. To effectively decompose this component, we will follow a structured architectural design process:

1. **Identify Core Responsibilities**: Determine the main functionalities of the Goose Testing Framework.
2. **Define Modules**: Based on the identified responsibilities, define distinct modules that encapsulate
   specific functionalities.
3. **Establish Interactions**: Define how these modules will interact with each other.
4. **Review and Refine**: Review the proposed design for coherence, efficiency, and maintainability.
5. **Implementation**: Proceed to implement the design in code.

## Rules:

-   Each module should have a single responsibility.
-   Modules should be loosely coupled and highly cohesive.
-   Use clear and descriptive names for modules and functions.
-   No need to maintain backwards compatibility; refactor as necessary.
-   You should never leave files or functionalities that exist only to maintain backwards compatibility,
    instead refactor the codebase to fit the new structure better and update all references.
