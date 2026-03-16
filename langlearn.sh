#!/bin/bash
# lang-learn: shell wrapper for the adaptive python implementation.

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required to run this script."
    exit 1
fi

# Path to the python script
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$DIR/langlearn.py"

# Run the python script with all arguments
python3 "$PYTHON_SCRIPT" "$@"
