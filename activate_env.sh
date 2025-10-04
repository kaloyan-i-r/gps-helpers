#!/bin/bash
# Activate GPS Helpers Environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Please run setup_environment.sh first."
    exit 1
fi

echo "Activating GPS Helpers environment..."
source "$VENV_DIR/bin/activate"
echo "Environment activated! You can now run:"
echo "  python gps_route_manager.py  # Start GUI"
echo "  python gpx_fix.py [options]  # Run GPX fixer"
echo "  deactivate                   # Exit environment"
