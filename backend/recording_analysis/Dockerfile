# Dockerfile for GCS Backend (FastAPI Server)

# Create from base image
FROM backend-base-image:latest

# Set working directory
WORKDIR /app

# Copy application code
COPY backend/recording_analysis ./

# Expose the backend port
EXPOSE ${RECORDING_ANALYSIS_BACKEND_PORT}

# Run the FastAPI server
CMD ["python", "query.py"]