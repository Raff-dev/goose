.PHONY: up app down migrations migrate

COMPOSE_FILE := example_system/docker-compose.yaml
STREAMLIT_PORT ?= 8501
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

# Launch the Streamlit test explorer
app:
	uv run streamlit run app/main.py --server.port $(STREAMLIT_PORT) --server.headless true

# Create new Django migrations
migrations:
	uv run python -m django makemigrations --settings=example_system.settings

# Apply Django migrations
migrate:
	uv run python -m django migrate --settings=example_system.settings
