# Makefile for SharePoint RAG Pipeline
# Vereinfacht die Docker-Operationen

.PHONY: help build test run dev clean logs status

# Default target
help: ## Show this help message
	@echo "SharePoint RAG Pipeline - Docker Commands"
	@echo "========================================"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Build targets
build: ## Build the production image (full version)
	docker compose build rag-pipeline

build-minimal: ## Build minimal image (PDF processing only)
	docker compose build --build-arg BUILD_MODE=minimal rag-pipeline

build-no-ai: ## Build without AI/ML dependencies
	docker compose build --build-arg INSTALL_AI_DEPS=false rag-pipeline

build-dev: ## Build the development image
	docker compose build --target development rag-dev

build-all: ## Build all images
	docker compose build

# Test targets
test: ## Run basic component tests
	docker compose -f docker-compose.test.yml up --build --abort-on-container-exit rag-test

test-unit: ## Run unit tests
	docker compose -f docker-compose.test.yml --profile test up --build --abort-on-container-exit rag-unittest

test-performance: ## Run performance tests
	docker compose -f docker-compose.test.yml --profile performance up --build --abort-on-container-exit rag-performance

test-integration: ## Run integration tests with ChromaDB
	docker compose -f docker-compose.test.yml --profile integration up --build --abort-on-container-exit

test-load: ## Run load tests
	docker compose -f docker-compose.test.yml --profile load up --build --abort-on-container-exit rag-load

test-all: test test-unit test-performance ## Run all tests

# Run targets
run: ## Run pipeline once with sample data
	docker compose up --build rag-pipeline

run-scheduled: ## Start scheduled pipeline service
	docker compose --profile scheduled up -d rag-scheduler

run-dev: ## Start development environment
	docker compose --profile dev up -d rag-dev

run-monitoring: ## Start with monitoring
	docker compose --profile monitoring up -d log-viewer

# Process targets with custom input
process: ## Process specific directory (usage: make process INPUT=/path/to/pdfs)
	@if [ -z "$(INPUT)" ]; then \
		echo "Usage: make process INPUT=/path/to/pdfs"; \
		exit 1; \
	fi
	docker run --rm \
		-v "$(INPUT):/app/input:ro" \
		-v "$(shell pwd)/data:/app/data" \
		sharepoint-rag-pipeline:latest \
		python run_pipeline.py /app/input --force-all

process-dry: ## Dry run for specific directory (usage: make process-dry INPUT=/path/to/pdfs)
	@if [ -z "$(INPUT)" ]; then \
		echo "Usage: make process-dry INPUT=/path/to/pdfs"; \
		exit 1; \
	fi
	docker run --rm \
		-v "$(INPUT):/app/input:ro" \
		sharepoint-rag-pipeline:latest \
		python run_pipeline.py /app/input --dry-run

# Management targets
logs: ## Show pipeline logs
	docker compose logs -f rag-pipeline

logs-scheduler: ## Show scheduler logs
	docker compose logs -f rag-scheduler

status: ## Show container status
	docker compose ps

stats: ## Show container resource usage
	docker stats --no-stream

# Development targets
shell: ## Open shell in running container
	docker compose exec rag-pipeline bash

shell-dev: ## Open shell in development container
	docker compose exec rag-dev bash

jupyter: ## Start Jupyter notebook in dev container
	docker compose exec rag-dev jupyter notebook --ip=0.0.0.0 --port=8888 --allow-root --no-browser

# Maintenance targets
clean: ## Stop and remove containers
	docker compose down

clean-all: ## Stop containers and remove volumes
	docker compose down -v

clean-images: ## Remove pipeline images
	docker rmi sharepoint-rag-pipeline:latest sharepoint-rag-pipeline:dev 2>/dev/null || true

restart: ## Restart pipeline service
	docker compose restart rag-pipeline

restart-scheduled: ## Restart scheduled service
	docker compose restart rag-scheduler

# Backup targets
backup: ## Backup pipeline data
	@mkdir -p backup
	docker run --rm \
		-v rag_data:/source \
		-v $(shell pwd)/backup:/backup \
		alpine tar czf /backup/rag-data-$(shell date +%Y%m%d_%H%M%S).tar.gz -C /source .
	@echo "Backup created in backup/ directory"

restore: ## Restore pipeline data (usage: make restore BACKUP=backup/rag-data-*.tar.gz)
	@if [ -z "$(BACKUP)" ]; then \
		echo "Usage: make restore BACKUP=backup/rag-data-YYYYMMDD_HHMMSS.tar.gz"; \
		echo "Available backups:"; \
		ls -la backup/rag-data-*.tar.gz 2>/dev/null || echo "No backups found"; \
		exit 1; \
	fi
	docker run --rm \
		-v rag_data:/target \
		-v $(shell pwd)/backup:/backup \
		alpine tar xzf /backup/$(notdir $(BACKUP)) -C /target
	@echo "Data restored from $(BACKUP)"

# Setup targets
setup: ## Initial setup - copy env file and build
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file - please edit it with your settings"; \
	fi
	$(MAKE) build

setup-dev: ## Setup development environment
	$(MAKE) setup
	$(MAKE) build-dev
	@echo "Development environment ready"

# Monitoring targets
monitor: ## Start monitoring dashboard
	docker compose --profile monitoring up -d log-viewer
	@echo "Log viewer available at http://localhost:8080"

health: ## Check pipeline health
	docker compose exec rag-pipeline python test_pipeline.py

# Quick targets for common workflows
quick-test: ## Quick test with minimal setup
	docker run --rm sharepoint-rag-pipeline:latest python test_pipeline.py

quick-run: ## Quick run with sample data
	$(MAKE) test

# CI/CD targets
ci-build: ## Build for CI/CD
	docker build -t sharepoint-rag-pipeline:$(shell git rev-parse --short HEAD) .
	docker tag sharepoint-rag-pipeline:$(shell git rev-parse --short HEAD) sharepoint-rag-pipeline:latest

ci-test: ## Run tests for CI/CD
	$(MAKE) test-all

ci-deploy: ## Deploy to registry (usage: make ci-deploy REGISTRY=your-registry.com)
	@if [ -z "$(REGISTRY)" ]; then \
		echo "Usage: make ci-deploy REGISTRY=your-registry.com"; \
		exit 1; \
	fi
	docker tag sharepoint-rag-pipeline:latest $(REGISTRY)/sharepoint-rag-pipeline:latest
	docker push $(REGISTRY)/sharepoint-rag-pipeline:latest

# Information targets
version: ## Show pipeline version
	@docker run --rm sharepoint-rag-pipeline:latest python -c "import sys; sys.path.insert(0, 'src'); from pipeline.orchestrator import ContextualRAGOrchestrator; print('Pipeline version: 2.0.0')"

info: ## Show system information
	@echo "Docker Information:"
	@echo "=================="
	@docker --version
	@docker compose --version
	@echo ""
	@echo "Pipeline Images:"
	@docker images | grep sharepoint-rag-pipeline || echo "No pipeline images found"
	@echo ""
	@echo "Running Containers:"
	@docker ps --filter "name=rag" || echo "No pipeline containers running"

# Platform-specific helpers
setup-windows: ## Windows-specific setup
	@echo "🪟 Windows Setup Instructions:"
	@echo "1. Ensure Docker Desktop is running"
	@echo "2. Enable WSL2 backend (recommended)"
	@echo "3. Share your drives in Docker Desktop settings"
	@echo "4. Use Windows-style paths in .env file"
	@echo "   Example: INPUT_DIR=C:\\Users\\YourName\\Documents\\PDFs"
	@echo ""
	@echo "Running docker-group-check..."
	@docker run hello-world || echo "❌ Docker not accessible. Check Docker Desktop installation."

setup-linux: ## Linux-specific setup
	@echo "🐧 Linux Setup Instructions:"
	@echo "Adding current user to docker group..."
	@sudo usermod -aG docker $$USER || echo "❌ Need sudo access to add user to docker group"
	@echo "✅ User added to docker group. Please log out and back in, or run: newgrp docker"
	@echo ""
	@echo "Testing docker access..."
	@docker run hello-world || echo "❌ Docker not accessible. Run: newgrp docker"

setup-macos: ## macOS-specific setup
	@echo "🍎 macOS Setup Instructions:"
	@echo "1. Ensure Docker Desktop is running"
	@echo "2. Check Docker Desktop → Preferences → Resources"
	@echo "3. Allocate sufficient memory (8GB+ recommended)"
	@echo ""
	@echo "Testing docker access..."
	@docker run hello-world || echo "❌ Docker not accessible. Check Docker Desktop."

# Cross-platform path normalization
normalize-path: ## Normalize INPUT path for current platform
ifndef INPUT
	@echo "Usage: make normalize-path INPUT=/path/to/dir"
else
ifeq ($(OS),Windows_NT)
	@echo "Windows path: $(subst /,\,$(INPUT))"
else
	@echo "Unix path: $(INPUT)"
endif
endif