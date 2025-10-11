#!/bin/bash

echo "Starting WebSocket Backend..."
echo "Backend will be available at: ws://localhost:8766/ws/gcs"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting server..."
python main.py
