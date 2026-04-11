# Goose release publish handover

This branch exists to hand off Goose release work to an agent running on the user machine with local publish credentials.

## Baseline

- Branch: `chore/release-publish-handover`
- Started from: `origin/main`
- Main commit at handover time: `ae28cb8` (`Merge pull request #37 from Raff-dev/fix/restore-github-landing-ctas`)

## What is already verified

These checks already passed during release preflight on a different machine:

1. Backend package build:
   - `uv build`
   - `uv run twine check dist/*`
2. Frontend package prepublish flow:
   - `cd web && npm install`
   - `cd web && npm run build`
   - `cd web && npm run build:cli`
   - `cd web && npm publish --dry-run`
3. Full test suite:
   - `make test`
   - Result: `197 passed`
   - Important: this required `OPENAI_API_KEY` to be present

There is no known code-level test failure to fix here. The earlier failing tests on the preflight machine were caused only by missing `OPENAI_API_KEY`.

## Why publish did not happen yet

The preflight machine did not have publish auth:

- no usable `.pypirc` / PyPI upload credentials
- no npm auth (`npm whoami` returned `ENEEDAUTH`)

This branch contains no secrets.

## Important repo behavior

`make pub` is the real publish command and will do both publishes immediately:

```bash
make pub
```

From `Makefile`:

- `pub-back`
  - bumps backend patch version with `uv version --bump patch`
  - rebuilds package
  - runs `twine check`
  - uploads via `.pypirc`
- `pub-front`
  - bumps frontend patch version with `npm version patch --no-git-tag-version`
  - installs deps
  - builds frontend and CLI bundle
  - publishes to npm

## Continue on the user machine

Run everything from the repo root unless noted otherwise.

### 1. Ensure local auth exists

Expected local inputs:

- `OPENAI_API_KEY` available in env before tests
- `.pypirc` present in repo root for `twine upload`
- npm auth available via `~/.npmrc` or repo-local `.npmrc`

Notes:

- `.pypirc` and `.npmrc` are already ignored by `.gitignore`
- do not commit credentials

### 2. Sanity-check auth before any publish attempt

```bash
test -f .pypirc
npm whoami
python3 - <<'PY'
import os
print("OPENAI_API_KEY present:", bool(os.environ.get("OPENAI_API_KEY")))
PY
```

If `OPENAI_API_KEY` is stored in a local env file, export it first, for example:

```bash
set -a
. ./.env
set +a
```

Adjust the env file path if your machine keeps Goose secrets elsewhere.

### 3. Re-run the exact release preflight locally

Do not start by changing tests. First provide the local env/auth inputs listed above and rerun the preflight as-is.

```bash
make test
rm -rf dist *.egg-info
uv build
uv run twine check dist/*
cd web && npm install && npm run build && npm run build:cli && npm publish --dry-run
```

Expected result:

- tests pass
- backend build passes
- frontend dry-run passes
- `npm whoami` succeeds

### 4. Run the real publish only after the preflight is green

```bash
make pub
```

## Expected file changes after publish

After a successful `make pub`, expect version bumps at least in:

- `pyproject.toml`
- `web/package.json`
- likely `web/package-lock.json`

Review the diff before committing.

## After publish

1. Verify the released versions on PyPI and npm.
2. Commit only the version bump files and any lockfile changes caused by publish prep.
3. Push the branch and open a PR back to `main` so the repo matches the published versions.

## Suggested local command sequence

```bash
git checkout chore/release-publish-handover

# export local secrets here

test -f .pypirc
npm whoami
make test
rm -rf dist *.egg-info
uv build
uv run twine check dist/*
cd web && npm install && npm run build && npm run build:cli && npm publish --dry-run
cd ..
make pub
git status --short
```
