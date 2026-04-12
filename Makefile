
.PHONY: up down migrations migrate web release-preflight pub pub-patch pub-minor pub-front pub-back test

export TWINE_CONFIG_FILE := $(abspath .pypirc)

COMPOSE_FILE := example_system/docker-compose.yaml
STREAMLIT_PORT ?= 8501
VERSION_BUMP ?= patch

up:
	docker compose -f $(COMPOSE_FILE) up -d postgres
	@echo "Waiting for Postgres container to become healthy..."
	@container_id=$$(docker compose -f $(COMPOSE_FILE) ps -q postgres); \
	if [ -z "$$container_id" ]; then \
		echo "Unable to determine postgres container ID"; \
		exit 1; \
	fi; \
	while true; do \
		status=$$(docker inspect -f '{{.State.Health.Status}}' $$container_id 2>/dev/null || echo "unknown"); \
		if [ "$$status" = "healthy" ]; then \
			break; \
		fi; \
		if [ "$$status" = "exited" ] || [ "$$status" = "dead" ]; then \
			echo "Postgres container exited with status $$status"; \
			exit 1; \
		fi; \
		sleep 1; \
	done
	$(MAKE) migrate

# Stop Docker Compose services and remove volumes
down:
	docker compose -f $(COMPOSE_FILE) down -v

# Create new Django migrations
migrations:
	uv run python -m django makemigrations --settings=example_system.settings

# Apply Django migrations
migrate:
	uv run python -m django migrate --settings=example_system.settings

# Start the web development server
web:
	cd web && npm run dev

# Run publish preflight without mutating package versions
release-preflight: test
	rm -rf dist *.egg-info
	uv build
	uv run twine check dist/*
	cd web && npm ci
	cd web && npm run build
	cd web && npm run build:cli
	cd web && npm pack --dry-run

# Publish both backend and frontend packages (defaults to patch)
pub:
	$(MAKE) pub-back VERSION_BUMP=$(VERSION_BUMP)
	$(MAKE) pub-front VERSION_BUMP=$(VERSION_BUMP)

# Publish both packages with an explicit patch bump
pub-patch:
	$(MAKE) pub VERSION_BUMP=patch

# Publish both packages with an explicit minor bump
pub-minor:
	$(MAKE) pub VERSION_BUMP=minor

# Publish backend package to PyPI
pub-back:
	uv version --bump $(VERSION_BUMP)
	rm -rf dist *.egg-info
	uv build
	uv run twine check dist/*
	uv run twine upload dist/* --config-file $(TWINE_CONFIG_FILE)

# Publish frontend package to npm
pub-front:
	cd web && npm version $(VERSION_BUMP) --no-git-tag-version
	cd web && npm ci
	cd web && npm run build
	cd web && npm run build:cli
	cd web && npm publish --access public

# Run backend unit tests with coverage
test:
	uv run coverage run -m pytest
	uv run coverage report
