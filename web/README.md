<h1 align="center">LLM Goose Dashboard 🪿</h1>

<p align="center">
  <strong>Web dashboard CLI for LLM Goose — the testing framework for LLM agents</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/llm-goose/"><img src="https://img.shields.io/pypi/v/llm-goose.svg?logo=pypi&label=PyPI" alt="PyPI"></a>
  <a href="https://www.npmjs.com/package/@llm-goose/dashboard-cli"><img src="https://img.shields.io/npm/v/@llm-goose/dashboard-cli.svg?logo=npm&label=npm" alt="npm"></a>
  <a href="https://github.com/Raff-dev/goose"><img src="https://img.shields.io/github/stars/Raff-dev/goose?style=social" alt="GitHub stars"></a>
</p>

---

This package provides the **web dashboard** for [LLM Goose](https://github.com/Raff-dev/goose), a Python testing framework for LLM agents.

## Features

- **Testing View** — Run and monitor agent tests with real-time results
- **Tooling View** — Interactively test your agent's tools in isolation
- **Chat View** — Chat with your agents directly in the browser
- **Full Execution Traces** — See every tool call, response, and validation result

<p align="center">
  <img src="https://raw.githubusercontent.com/Raff-dev/goose/main/images/dashboard_view.png" alt="Dashboard screenshot" width="80%">
</p>

## Install

```bash
# Install the dashboard CLI globally
npm install -g @llm-goose/dashboard-cli

# Or use npx without installing
npx @llm-goose/dashboard-cli
```

## Usage

```bash
# Start the API server (requires llm-goose Python package)
pip install llm-goose
goose api

# In another terminal, start the dashboard
goose-dashboard
```

The dashboard will open at `http://localhost:8729` and connect to the API at `http://localhost:8730`.

### Custom API URL

```bash
goose-dashboard --api-url http://localhost:9000
```

## Requirements

This dashboard requires the [llm-goose](https://pypi.org/project/llm-goose/) Python package to be installed and running:

```bash
pip install llm-goose
goose init        # Scaffold a new project
goose api         # Start the API server
```

## Links

- 📦 [PyPI Package (llm-goose)](https://pypi.org/project/llm-goose/)
- 🐙 [GitHub Repository](https://github.com/Raff-dev/goose)
- 📖 [Documentation](https://github.com/Raff-dev/goose#readme)

## License

MIT © [Rafał Łazicki](https://github.com/Raff-dev)
