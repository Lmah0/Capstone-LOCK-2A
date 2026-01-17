# Dockerfile for GCS Backend
FROM python:3.10.7-slim

# Set working directory
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all other files from your backend folder
# We copy the content bc Docker doesnt have access to git folder
COPY backend/gcs ./

# Expose the backend port (value from .env)
EXPOSE ${GCS_BACKEND_PORT}

# Run the FastAPI server
CMD ["python", "server.py"]