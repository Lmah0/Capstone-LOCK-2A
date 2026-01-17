# Dockerfile for GCS Backend (FastAPI Server)
FROM python:3.10.7-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/recording_analysis ./

# Expose the backend port
EXPOSE ${RECORDING_ANALYSIS_BACKEND_PORT}

# Run the FastAPI server
CMD ["python", "query.py"]