#!/bin/bash
# Starts either GCS or RecordingAnalysis backend using shared virtual environment

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
    echo "  $0 gcs        # Start GCS backend"
    echo "  $0 recording  # Start RecordingAnalysis backend"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating shared virtual environment..."
source "$VENV_PATH/bin/activate"

case "$1" in
    "gcs")
        echo "Starting GCS Backend..."
        cd "$PROJECT_ROOT/GCS/backend"
        python server.py
        ;;
    "recording")
        echo "Starting RecordingAnalysis Backend..."
        cd "$PROJECT_ROOT/RecordingAnalysis/backend"
        python query.py
        ;;
    *)
        echo "Invalid option: $1"
        echo "Use 'gcs' or 'recording'"
        exit 1
        ;;
esac