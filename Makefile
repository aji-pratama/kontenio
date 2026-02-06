# AI Video Factory - Essential Makefile
# ====================================

.PHONY: help setup dev video render clean

# Default shell
SHELL := /bin/bash
PYTHON := python
DJANGO := cd backend && $(PYTHON) manage.py

# --- Core Commands ---

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup: ## Install dependencies, migrate, and setup environment
	npm install
	cd backend && pip install -r requirements.txt
	$(DJANGO) migrate
	@mkdir -p backend/media/raw backend/media/assets backend/media/output backend/media/props
	@# Create symlink if it doesn't exist
	@ln -sfn $(PWD)/backend/media $(PWD)/public/media
	@echo "✅ Setup complete! Use 'make dev' to start."

dev: ## Run Django Admin AND Remotion Studio concurrently
	@echo "🚀 Starting Django Admin (Port 9000) and Remotion Studio..."
	@# Run both in background and wait. Kill both on Ctrl+C.
	@trap 'kill 0' SIGINT; \
	 (cd backend && $(PYTHON) manage.py runserver 9000) & \
	 (npx remotion studio) & \
	 wait

# --- Video Operations ---

video: ## Process video (Usage: make video INPUT=path/to/video.mp4)
	@if [ -z "$(INPUT)" ]; then echo "❌ Error: INPUT is required. Example: make video INPUT=my_video.mp4"; exit 1; fi
	$(DJANGO) make_video --input="$(INPUT)"

render: ## Render video using latest generated props
	npx remotion render SplitScreen out/video.mp4 --props=public/media/render_props.json

# --- Utilities ---

clean: ## Remove temporary files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf out/*
	@echo "✨ Cleaned up!"
