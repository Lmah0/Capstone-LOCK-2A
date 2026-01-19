# User Application Setup & Run Guide
---

## 1. Setup the .env variables from this guide
- Web Guide: [Setup and Environment Variables](https://capstone-lock-2a.atlassian.net/wiki/spaces/CL/pages/15532033)
- Note: If you **Do Not** have the AWS keys, follow the **Optional Step** from the same guide.

## 2. Download Docker Desktop
- [Docker Desktop: The #1 Containerization Tool for Developers | Docker](https://www.docker.com/products/docker-desktop/)
- Verify its installation by checking versions in your terminal:
  - `docker compose version`
  - `docker --version`

## 3. First-Time Setup
- Open your terminal.
- Build base layer:
  - `make build-base`
- Build application images:
  - `make build-images`
> *Note:* Run these commands only during your **initial setup** or when **configuration files change** (e.g., updates to Dockerfile, package.json, or requirements.txt).

## 4. Running Services
- To start the application, choose a Profile Name from the list below:
  - gcs
  - recording-analysis
  - all
- Replace `<name>` with your chosen profile:
  - `make <name>`

## 5. Stopping Services
- `make down`

# Miscellaneous Commands
### To Check Logs:
- Either check via Docker Desktop application by clicking on the container.
- Or run in terminal:
```bash
docker compose logs -f
docker compose logs -f {service_name} # Replace {service_name} with your service name (e.g., frontend-gcs)
```
### Help & Documentation:
- `make help`
### Deep Clean & Delete Everything:
- `make clean`