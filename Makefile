# AI Video Factory - Makefile
# ===========================

# Default shell
SHELL := /bin/bash

# Python environment
PYTHON := python
DJANGO := cd backend && $(PYTHON) manage.py

# Remotion
REMOTION := npx remotion

# ===========================
# Development
# ===========================

.PHONY: dev
dev: ## Run Remotion studio for preview
	$(REMOTION) studio

.PHONY: admin
admin: ## Run Django admin server
	$(DJANGO) runserver

.PHONY: shell
shell: ## Open Django shell
	$(DJANGO) shell

# ===========================
# Database
# ===========================

.PHONY: migrate
migrate: ## Run Django migrations
	$(DJANGO) migrate

.PHONY: makemigrations
makemigrations: ## Create new migrations
	$(DJANGO) makemigrations

.PHONY: superuser
superuser: ## Create superuser
	$(DJANGO) createsuperuser

# ===========================
# Video Processing
# ===========================

.PHONY: render
render: ## Render video with default props
	$(REMOTION) render SplitScreen out/output.mp4 --props=public/media/render_props.json

.PHONY: video
video: ## Process video (usage: make video INPUT=myfile.mp4)
	$(DJANGO) make_video --input="$(INPUT)"

.PHONY: video-mock
video-mock: ## Process video with mock data (usage: make video-mock INPUT=myfile.mp4)
	$(DJANGO) make_video --input="$(INPUT)" --mock

.PHONY: video-props
video-props: ## Generate props only without rendering (usage: make video-props INPUT=myfile.mp4)
	$(DJANGO) make_video --input="$(INPUT)" --mock --skip-render

# ===========================
# Setup
# ===========================

.PHONY: install
install: ## Install all dependencies
	npm install
	cd backend && pip install -r requirements.txt

.PHONY: setup
setup: install migrate ## Full setup (install + migrate)
	@echo "✅ Setup complete!"
	@echo "   - Run 'make admin' to start Django admin"
	@echo "   - Run 'make dev' to start Remotion studio"

.PHONY: symlink
symlink: ## Create media symlink for Remotion
	ln -sfn $(PWD)/backend/media $(PWD)/public/media

# ===========================
# Linting & Testing
# ===========================

.PHONY: lint
lint: ## Run linters
	npm run lint

.PHONY: check
check: ## Run Django checks
	$(DJANGO) check

# ===========================
# Help
# ===========================

.PHONY: help
help: ## Show this help message
	@echo "AI Video Factory - Available Commands"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
