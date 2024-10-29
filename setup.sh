#!/bin/bash

# Exit on error
set -e

echo "=== Setting up AI-Enhanced Treatment Recommendation System ==="

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Verify setup
echo "Verifying setup..."
python verify_setup.py

if [ $? -eq 0 ]; then
    echo "
Setup completed successfully!

To start the system:
1. Activate the virtual environment: source venv/bin/activate
2. Run the system: python run_system.py

For more information, see README.md
"
else
    echo "
Setup encountered some issues. Please fix the reported problems and try again.
"
    exit 1
fi
