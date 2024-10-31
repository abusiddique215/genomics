#!/bin/bash

# Exit on error
set -e

# Function to print messages
print_message() {
    echo "===> $1"
}

# Function to check command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_message "Error: $1 is required but not installed."
        exit 1
    fi
}

# Check required commands
print_message "Checking required commands..."
check_command python3
check_command pip
check_command git

# Set up Python virtual environment
print_message "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
print_message "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_message "Installing dependencies..."
pip install -r requirements.txt

# Set up pre-commit hooks
print_message "Setting up pre-commit hooks..."
pre-commit install

# Create necessary directories
print_message "Creating necessary directories..."
mkdir -p logs
mkdir -p data
mkdir -p models

# Set up DynamoDB Local
print_message "Setting up DynamoDB Local..."
if [ ! -f dynamodb_local_latest.tar.gz ]; then
    curl -O https://s3.us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.tar.gz
    tar xzf dynamodb_local_latest.tar.gz
    rm dynamodb_local_latest.tar.gz
fi

# Set up environment variables
print_message "Setting up environment variables..."
if [ ! -f .env ]; then
    cp .env.example .env
    print_message "Please update .env with your configuration"
fi

# Initialize git if not already initialized
if [ ! -d .git ]; then
    print_message "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit"
fi

# Create AWS credentials file if it doesn't exist
print_message "Setting up AWS credentials..."
mkdir -p ~/.aws
if [ ! -f ~/.aws/credentials ]; then
    cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = your_access_key
aws_secret_access_key = your_secret_key
region = us-west-2
EOF
    print_message "Please update ~/.aws/credentials with your AWS credentials"
fi

# Set up logging
print_message "Setting up logging..."
mkdir -p logs
touch logs/app.log

# Set up test data
print_message "Setting up test data..."
mkdir -p tests/data
if [ ! -f tests/data/test_patients.json ]; then
    echo '[]' > tests/data/test_patients.json
fi

# Run tests to verify setup
print_message "Running tests..."
pytest tests/ -v

# Start services
print_message "Starting services..."
./start_services.py &

print_message "Setup completed successfully!"
print_message "Next steps:"
print_message "1. Update .env with your configuration"
print_message "2. Update AWS credentials in ~/.aws/credentials"
print_message "3. Start development with: source venv/bin/activate"
