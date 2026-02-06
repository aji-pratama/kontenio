# AI Video Factory - Centralized Control Center
# ============================================

.PHONY: help build up down restart status logs logs-worker logs-beat logs-studio migrate-db shell c-video c-video-async c-test clean create-superuser

# Configuration
SHELL := /bin/bash
PODMAN := podman-compose
WEB_CONTAINER := kontenio_web
WORKER_CONTAINER := kontenio_worker

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# --- Deployment Commands ---

build: ## Build or rebuild services
	$(PODMAN) build

up: ## Start all services (Frontend, Web, Worker, Beat, DB, Redis)
	$(PODMAN) up -d
	@echo "🚀 Kontenio is UP!"
	@echo "🌐 Frontend:        http://localhost:5173"
	@echo "🌐 Django Admin:    http://localhost:8001/admin"
	@echo "📡 API Documentation: http://localhost:8001/api/docs"

down: ## Stop and remove all services
	$(PODMAN) down

restart: ## Restart all services
	$(PODMAN) restart

status: ## Check service status
	$(PODMAN) ps

logs: ## Tail web logs
	podman logs -f kontenio_web

logs-worker: ## Tail worker logs
	podman logs -f kontenio_worker

logs-beat: ## Tail beat logs
	podman logs -f kontenio_beat

logs-frontend: ## Tail frontend logs
	podman logs -f kontenio_frontend

create-superuser: ## Create a Django admin superuser
	podman exec -it $(WEB_CONTAINER) python3 backend/manage.py createsuperuser

# --- Database & Shell ---

migrate-db: ## Run Django migrations inside container
	podman exec -it $(WEB_CONTAINER) python3 backend/manage.py makemigrations
	podman exec -it $(WEB_CONTAINER) python3 backend/manage.py migrate

shell: ## Enter the web container shell
	podman exec -it $(WEB_CONTAINER) /bin/bash

# --- Video Operations (Run inside container) ---

c-video: ## Process video (Usage: make c-video INPUT=clip.mp4)
	@if [ -z "$(INPUT)" ]; then echo "❌ Error: INPUT is required."; exit 1; fi
	podman exec -it $(WEB_CONTAINER) python3 backend/manage.py make_video --input="$(INPUT)"

render-video: ## Alias for c-video (Usage: make render-video INPUT=clip.mp4)
	@$(MAKE) c-video INPUT="$(INPUT)"

c-video-async: ## Process via Celery (Usage: make c-video-async INPUT=clip.mp4 MOCK=true)
	@if [ -z "$(INPUT)" ]; then echo "❌ Error: INPUT is required."; exit 1; fi
	$(eval MOCK_FLAG := $(if $(filter true,$(MOCK)),--mock,))
	podman exec -it $(WEB_CONTAINER) python3 backend/manage.py make_video --input="$(INPUT)" --async-task $(MOCK_FLAG)

c-test: ## Run backend tests inside container
	podman exec -it $(WEB_CONTAINER) python3 backend/manage.py test video.tests

# --- Maintenance ---

clean: ## Remove temp files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf out/*
	@echo "✨ Cleaned up!"

nuke: ## Force destroy all project containers and images
	@echo "💥 Nuking environment..."
	-$(PODMAN) down
	-podman pod rm -f -a
	-podman rm -f -a
	-podman volume prune -f
	@echo "💀 Clean state achieved. Run 'make build' to start fresh."
