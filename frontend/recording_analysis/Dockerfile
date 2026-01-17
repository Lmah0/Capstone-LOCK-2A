# Dockerfile for GCS Frontend (Next.js)
FROM node:24-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY frontend/recording_analysis/package*.json ./

# Install dependencies
RUN npm ci

# Copy all other files from your frontend folder
# We copy the content bc Docker doesnt have access to git folder
COPY frontend/recording_analysis ./

# Expose port
EXPOSE ${RECORDING_ANALYSIS_FRONTEND_PORT}

# Run development server
CMD ["npm", "run", "dev"]