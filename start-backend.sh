#!/bin/bash
# Starts specified backend server(s) after ensuring the virtual environment is set up.

set -e  # Exit on any error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    ./setup-backend-env.sh
fi

# Check argument
if [ $# -eq 0 ]; then
    echo "Usage: $0 [gcs|recording]"
    echo ""
    echo "Examples:"
    echo "  $0 all        # Start all backends"
    echo "  $0 gcs        # Start GCS backend"
    echo "  $0 recording  # Start RecordingAnalysis backend"
    echo "  $0 rpi       # Start RPi backend"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating shared virtual environment..."
if [ -f "$VENV_PATH/Scripts/activate" ]; then
    # Windows (Git Bash)
    source "$VENV_PATH/Scripts/activate"
elif [ -f "$VENV_PATH/bin/activate" ]; then
    # Linux / macOS / WSL
    source "$VENV_PATH/bin/activate"
else
    echo "❌ Could not find venv activation script."
    exit 1
fi

case "$1" in
    "all")
        echo "Starting all backends..."
        
        echo "Starting GCS Backend..."
        (cd "$PROJECT_ROOT/GCS/backend" && python server.py) &

        echo "Starting RecordingAnalysis Backend..."
        (cd "$PROJECT_ROOT/RecordingAnalysis/backend" && python query.py) &

        echo "Starting RPi Backend..."
        (cd "$PROJECT_ROOT/Drone/flightComputer" && python server.py) &

        wait
        ;;
    "gcs")
        echo "Starting GCS Backend..."
        cd "$PROJECT_ROOT/GCS/backend"
        python server.py
        python AiStreamClient.py
        ;;
    "recording")
        echo "Starting RecordingAnalysis Backend..."
        cd "$PROJECT_ROOT/RecordingAnalysis/backend"
        python query.py
        ;;
    "rpi")
        echo "Starting RPi Backend..."
        cd "$PROJECT_ROOT/Drone/flightComputer"
        python server.py
        ;;
    *)
        echo "Invalid option: $1"
        echo "Use 'gcs' or 'recording'"
        exit 1
        ;;
esac