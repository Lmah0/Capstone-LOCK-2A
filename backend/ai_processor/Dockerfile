# Dockerfile for AI Processor
FROM python:3.10.7-slim

# Set working directory
WORKDIR /app

# Install system dependencies required by OpenCV, Torch, etc.
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

# Copy requirements first (cache-friendly)
COPY requirements.txt .

# Install Python dependencies (cached unless requirements.txt changes)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY backend/ai_processor ./

# Create startup script (in /usr/local/bin so volume mount doesn't overwrite it)
RUN printf '#!/bin/bash\nset -e\ncd /app\npython main.py\n' > /usr/local/bin/start.sh \
    && chmod +x /usr/local/bin/start.sh

# Run the AI processor
CMD ["/usr/local/bin/start.sh"]

