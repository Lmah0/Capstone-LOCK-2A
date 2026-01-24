# Docker Makefile

.PHONY: build-base build-images gcs recording all down clean help check-base

BASE_IMAGE = backend-base-image:latest

help:
	@echo "Usage:"
	@echo "  make build-base     - Build shared base image"
	@echo "  make build-images   - Build all compose images"
	@echo "  make gcs            - Run GCS stack"
	@echo "  make recording      - Run Recording Analysis stack"
	@echo "  make all            - Run all services"
	@echo "  make down           - Stop all containers"
	@echo "  make clean          - Remove all images & volumes"

build-base:
	docker build -t $(BASE_IMAGE) -f docker/base/Dockerfile.python-base .

build-images:
	docker compose --profile all build

check-base:
	@docker image inspect $(BASE_IMAGE) >/dev/null 2>&1 || \
	(echo "Base image missing. Run: make build-base" && exit 1)

gcs: check-base
	docker compose --profile gcs up -d

recording: check-base
	docker compose --profile recording-analysis up -d

all: check-base
	docker compose --profile all up -d

down:
	docker compose --profile all down

clean: # Only run this if you want to remove everything
	docker compose --profile all down --rmi local --volumes --remove-orphans
	docker rmi -f $(BASE_IMAGE)
