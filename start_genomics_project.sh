#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")"

# Activate the virtual environment
source venv/bin/activate

# Set environment variables
set -a
source .env
set +a

# Check AWS permissions
echo "Checking AWS permissions..."
./update_iam_permissions.sh

# Start the services
python start_services.py