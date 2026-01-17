# Dockerfile for GCS Frontend (Next.js)
FROM node:24-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY frontend/gcs/package*.json ./

# Install dependencies
RUN npm ci

# Copy all other files from your frontend folder
# Source: C:\Users\Eric\...\frontend\gcs\*
# Destination: /app/ (in container)
# We copy the content bc Docker doesnt have access to git folder
COPY frontend/gcs ./

# Expose port
EXPOSE ${GCS_FRONTEND_PORT}

# Run development server
CMD ["npm", "run", "dev"]