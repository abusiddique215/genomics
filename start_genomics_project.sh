#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")"

# Activate the virtual environment
source venv/bin/activate

# Set environment variables
set -a
source .env
set +a

# Update IAM permissions
echo "Updating IAM permissions..."
./update_iam_permissions.sh

# Start the services
python start_services.py