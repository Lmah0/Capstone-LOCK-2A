# Dockerfile for AI Processor

# Create from base image
FROM backend-base-image:latest

# Set working directory
WORKDIR /app

# Copy application source code
COPY . .

# Create startup script (in /usr/local/bin so volume mount doesn't overwrite it)
RUN printf '#!/bin/bash\nset -e\ncd /app\npython main.py\n' > /usr/local/bin/start.sh \
    && chmod +x /usr/local/bin/start.sh

# Run the AI processor
CMD ["/usr/local/bin/start.sh"]

