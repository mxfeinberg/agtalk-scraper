# Makefile for AgTalk Scraper Docker operations

# Variables
IMAGE_NAME := agtalk-scraper
IMAGE_TAG := $(shell date +%Y-%m-%d)
PLATFORM := linux/arm64,linux/amd64
TAR_FILE := agtalk-scraper.tar

# Default target
.DEFAULT_GOAL := help

# Help target
.PHONY: help
help: ## Show this help message
	@echo "AgTalk Scraper Docker Build System"
	@echo "=================================="
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# Build for Apple Silicon (ARM64)
.PHONY: build-arm64
build-arm64: ## Build Docker image for Apple Silicon (ARM64)
	@echo "Building Docker image for Apple Silicon (ARM64)..."
	docker build --platform linux/arm64 -t $(IMAGE_NAME):$(IMAGE_TAG) .
	@echo "✓ Built $(IMAGE_NAME):$(IMAGE_TAG) for ARM64"

# Build for AMD64
.PHONY: build-amd64
build-amd64: ## Build Docker image for x86 (AMD64)
	@echo "Building Docker image for x86 (AMD64)..."
	docker build --platform linux/amd64 -t $(IMAGE_NAME):$(IMAGE_TAG) .
	@echo "✓ Built $(IMAGE_NAME):$(IMAGE_TAG) for AMD64"

# Build for multi-platform (ARM64 + AMD64)
.PHONY: build-multi
build-multi: ## Build multi-platform Docker image (ARM64 + AMD64)
	@echo "Building multi-platform Docker image..."
	docker buildx build --platform $(PLATFORM) -t $(IMAGE_NAME):$(IMAGE_TAG) .
	@echo "✓ Built $(IMAGE_NAME):$(IMAGE_TAG) for multiple platforms"

# Build standard image (current platform)
.PHONY: build
build: ## Build Docker image for current platform
	@echo "Building Docker image for current platform..."
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .
	@echo "✓ Built $(IMAGE_NAME):$(IMAGE_TAG)"

# Export AMD64 image to tar file
.PHONY: export
export: ## Build and export AMD64 Docker image to tar file
	@echo "Building and exporting AMD64 Docker image to $(TAR_FILE)..."
	docker build --platform linux/amd64 -t $(IMAGE_NAME):$(IMAGE_TAG) .
	docker save $(IMAGE_NAME):$(IMAGE_TAG) -o $(TAR_FILE)
	@echo "✓ Exported AMD64 image to $(TAR_FILE)"
	@echo "File size: $$(du -h $(TAR_FILE) | cut -f1)"

# Run the containerized scraper
.PHONY: run
run: ## Run the containerized scraper
	@echo "Running AgTalk scraper container..."
	docker run --rm \
		-e DATABASE_URL \
		-e PGHOST \
		-e PGPORT \
		-e PGDATABASE \
		-e PGUSER \
		-e PGPASSWORD \
		$(IMAGE_NAME):$(IMAGE_TAG)

# Run with custom environment file
.PHONY: run-env
run-env: ## Run with custom .env file
	@echo "Running AgTalk scraper with environment file..."
	docker run --rm --env-file .env $(IMAGE_NAME):$(IMAGE_TAG)

# Interactive shell in container
.PHONY: shell
shell: ## Open interactive shell in container
	@echo "Opening shell in container..."
	docker run --rm -it \
		-e DATABASE_URL \
		-e PGHOST \
		-e PGPORT \
		-e PGDATABASE \
		-e PGUSER \
		-e PGPASSWORD \
		--entrypoint /bin/bash \
		$(IMAGE_NAME):$(IMAGE_TAG)

# Clean up Docker images and containers
.PHONY: clean
clean: ## Clean up Docker images and tar files
	@echo "Cleaning up Docker images and files..."
	-docker rmi $(IMAGE_NAME):$(IMAGE_TAG) 2>/dev/null || true
	-rm -f $(TAR_FILE) 2>/dev/null || true
	@echo "✓ Cleanup complete"

# Show image information
.PHONY: info
info: ## Show Docker image information
	@echo "Docker Image Information:"
	@echo "========================"
	@echo "Image Name: $(IMAGE_NAME):$(IMAGE_TAG)"
	@if docker image inspect $(IMAGE_NAME):$(IMAGE_TAG) >/dev/null 2>&1; then \
		echo "Status: Built"; \
		echo "Size: $$(docker image inspect $(IMAGE_NAME):$(IMAGE_TAG) --format='{{.Size}}' | numfmt --to=iec)"; \
		echo "Created: $$(docker image inspect $(IMAGE_NAME):$(IMAGE_TAG) --format='{{.Created}}' | cut -d'T' -f1)"; \
		echo "Architecture: $$(docker image inspect $(IMAGE_NAME):$(IMAGE_TAG) --format='{{.Architecture}}')"; \
	else \
		echo "Status: Not built"; \
	fi
	@if [ -f $(TAR_FILE) ]; then \
		echo "Tar file: $(TAR_FILE) ($$(du -h $(TAR_FILE) | cut -f1))"; \
	else \
		echo "Tar file: Not exported"; \
	fi

# Quick build and test
.PHONY: test
test: build ## Build and test the container
	@echo "Testing container functionality..."
	docker run --rm $(IMAGE_NAME):$(IMAGE_TAG) uv run main.py --help
	@echo "✓ Container test passed"

# All-in-one: build, test, and export
.PHONY: all
all: build test export ## Build, test, and export the image
	@echo "✓ Complete build pipeline finished"
	@echo "Image exported to: $(TAR_FILE)"