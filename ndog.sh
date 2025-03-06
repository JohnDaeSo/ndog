#!/bin/bash
# Simple launcher script for ndog

# Find the Python executable
PYTHON=$(command -v python3 || command -v python)

if [ -z "$PYTHON" ]; then
    echo "Error: Python not found. Please install Python 3."
    exit 1
fi

# Run the ndog module with all arguments
$PYTHON -m ndog.cli "$@" 