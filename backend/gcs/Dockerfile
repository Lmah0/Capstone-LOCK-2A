# Dockerfile for GCS Backend

# Create from base image
FROM backend-base-image:latest

# Set working directory
WORKDIR /app

# Copy all other files from your backend folder
# We copy the content bc Docker doesnt have access to git folder
COPY . .

# Expose the backend port (value from .env)
EXPOSE ${GCS_BACKEND_PORT}

# Run the FastAPI server
CMD ["python", "server.py"]