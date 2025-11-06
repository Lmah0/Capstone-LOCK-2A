#!/bin/bash

# Backend Environment Setup Script
# Creates a shared virtual environment for both GCS and RecordingAnalysis backends

set -e  # Exit on any error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"

echo "Setting up shared backend environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment at $VENV_PATH"
    python3 -m venv "$VENV_PATH"
else
    echo "Virtual environment already exists at $VENV_PATH"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r "$PROJECT_ROOT/requirements.txt"

echo "Backend environment setup complete!"
echo ""
echo "To activate the environment manually, run:"
echo "source $VENV_PATH/bin/activate"
echo ""
echo "To start backends:"
echo "cd $PROJECT_ROOT/GCS/backend && ../../start-backend.sh gcs"
echo "cd $PROJECT_ROOT/RecordingAnalysis/backend && ../../start-backend.sh recording"