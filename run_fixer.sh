#!/bin/bash
# GPX Fixer Launcher

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Please run setup_environment.sh first."
    exit 1
fi

echo "Starting GPX Fixer..."
source "$VENV_DIR/bin/activate"
python "$SCRIPT_DIR/gpx_fix.py" "$@"
