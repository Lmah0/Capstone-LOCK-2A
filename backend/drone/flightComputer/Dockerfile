# Dockerfile for GCS Backend (FastAPI Server)

# Create from base image
FROM backend-base-image:latest

# Set working directory
WORKDIR /app
# Copy application code
COPY . .

# Expose the backend port (value from .env)
EXPOSE ${RPI_BACKEND_PORT}

# Run the FastAPI server
CMD ["python", "server.py"]