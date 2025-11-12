#!/usr/bin/env bash
set -euo pipefail

# Allow overriding the command after migrations: ./entrypoint.sh <cmd>
PROJECT_ROOT="$(cd "$(dirname "$0")"/.. && pwd)"

cd "$PROJECT_ROOT"

uv run python -m django makemigrations --settings=example_system.settings --noinput
uv run python -m django migrate --settings=example_system.settings

if [ "$#" -gt 0 ]; then
    exec "$@"
fi
