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
   - `cd web && npm ci`
   - `cd web && npm run build`
   - `cd web && npm run build:cli`
   - package contents/build path verified
3. Full test suite:
   - `make test`
   - Result at handover time: `197 passed`

At handover time there was no remaining product-code failure blocking release work; the only failing preflight issue was the old test-harness coupling to `OPENAI_API_KEY`, and that is now fixed.

Update after the handover branch audit on the current machine:

- Goose test harness was fixed to lazily initialize `AgentValidator`
- current suite now passes without `OPENAI_API_KEY`
- current result: `199 passed`

## Why publish did not happen yet

The preflight machine did not have publish auth:

- no usable `.pypirc` / PyPI upload credentials
- no npm auth (`npm whoami` returned `ENEEDAUTH`)

This branch contains no secrets.

## Important repo behavior

Goose now has a safer release flow:

- `make release-preflight`
  - runs tests
  - rebuilds the Python package and runs `twine check`
  - installs frontend deps with `npm ci`
  - builds the frontend/CLI bundle
  - runs `npm pack --dry-run` so package contents are validated without failing on already-published npm versions
- `make pub`
  - publishes both packages immediately
  - defaults to `VERSION_BUMP=patch`
- `make pub-minor`
  - publishes both packages with a minor bump
- `make pub VERSION_BUMP=minor`
  - equivalent explicit form of `make pub-minor`

For the planned next release, use:

```bash
make pub-minor
```

From `Makefile`:

- `pub-back`
  - bumps backend version with `uv version --bump $(VERSION_BUMP)`
  - rebuilds package
  - runs `twine check`
  - uploads via `.pypirc`
- `pub-front`
  - bumps frontend version with `npm version $(VERSION_BUMP) --no-git-tag-version`
  - installs deps with `npm ci`
  - builds frontend and CLI bundle
  - publishes to npm

## Continue on the user machine

Run everything from the repo root unless noted otherwise.

### 1. Ensure local auth exists

Expected local inputs:

- `.pypirc` present in repo root for `twine upload`
- npm auth available via `~/.npmrc` or repo-local `.npmrc`

Notes:

- `.pypirc`, `.npmrc`, `.env`, and `.env.*` are ignored by `.gitignore`; `.env.example` remains the only tracked env template
- do not commit credentials
- `OPENAI_API_KEY` is no longer required for the current Goose test suite
- pre-commit + CI now enforce `detect-private-key`, `detect-secrets`, and a guard that rejects tracked `.env*`, `.pypirc`, and `.npmrc` files

### 2. Sanity-check auth before any publish attempt

```bash
test -f .pypirc
npm whoami
```

### 3. Re-run the exact release preflight locally

First provide the local auth inputs listed above and rerun the preflight.

```bash
make release-preflight
```

Expected result:

- tests pass
- backend build passes
- frontend package dry-run passes
- `npm whoami` succeeds

### 4. Run the real publish only after the preflight is green

```bash
make pub-minor
```

## Expected file changes after publish

After a successful `make pub-minor`, expect version bumps at least in:

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

test -f .pypirc
npm whoami
make release-preflight
make pub-minor
git status --short
```
