#!/bin/bash
# Installation script for ndog

set -e

echo "Installing ndog - Enhanced Network Communication Tool"
echo "===================================================="

# Find the Python executable
PYTHON=$(command -v python3 || command -v python)

if [ -z "$PYTHON" ]; then
    echo "Error: Python not found. Please install Python 3."
    exit 1
fi

# Check Python version
PY_VERSION=$($PYTHON --version | awk '{print $2}')
PY_MAJOR=$(echo $PY_VERSION | cut -d. -f1)
PY_MINOR=$(echo $PY_VERSION | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 8 ]); then
    echo "Error: ndog requires Python 3.8 or later."
    echo "Current version: $PY_VERSION"
    exit 1
fi

echo "Python $PY_VERSION found."

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install the package in development mode
echo "Installing ndog..."
pip install -e .

# Create a symlink to ndog in /usr/local/bin if not there
if [ ! -f "/usr/local/bin/ndog" ]; then
    echo "Creating symlink in /usr/local/bin..."
    
    # First check if we have permissions
    if [ -w "/usr/local/bin" ]; then
        ln -sf "$(pwd)/ndog.sh" /usr/local/bin/ndog
    else
        echo "Requesting sudo permissions to create symlink..."
        sudo ln -sf "$(pwd)/ndog.sh" /usr/local/bin/ndog
    fi
    
    echo "Symlink created."
else
    echo "Symlink already exists in /usr/local/bin."
fi

echo "Installation complete!"
echo "You can now run 'ndog' from anywhere."
echo "For usage information, run 'ndog --help'." 