#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
if ! command_exists python3; then
    echo "Python 3 is not installed. Please install it and try again."
    exit 1
fi

if ! command_exists pip; then
    echo "pip is not installed. Please install it and try again."
    exit 1
fi

if ! command_exists virtualenv; then
    echo "virtualenv is not installed. Installing now..."
    pip install virtualenv
fi

# Navigate to the project directory
cd "$(dirname "$0")"

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install or upgrade pip, setuptools, and wheel
pip install --upgrade pip setuptools wheel

# Install project dependencies
echo "Installing project dependencies..."
pip install -r requirements.txt

# Set up environment variables
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat << EOF > .env
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_DEFAULT_REGION=your_aws_region
S3_BUCKET_NAME=your_s3_bucket_name
RAG_SERVICE_URL=http://localhost:8006
OPENAI_API_KEY=your_openai_api_key
EOF
    echo "Please edit the .env file with your actual credentials and settings."
    exit 1
fi

# Source environment variables
set -a
source .env
set +a

# Run AWS CLI configure if credentials are not set
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "AWS credentials not found. Running 'aws configure'..."
    aws configure
fi

# Create genomics-api-user if it doesn't exist
if ! aws iam get-user --user-name genomics-api-user &> /dev/null; then
    echo "Creating genomics-api-user..."
    aws iam create-user --user-name genomics-api-user
    aws iam create-access-key --user-name genomics-api-user > access_key.json
    export AWS_ACCESS_KEY_ID=$(jq -r .AccessKey.AccessKeyId access_key.json)
    export AWS_SECRET_ACCESS_KEY=$(jq -r .AccessKey.SecretAccessKey access_key.json)
    echo "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" >> .env
    echo "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" >> .env
    rm access_key.json
fi

# Update IAM permissions
echo "Updating IAM permissions..."
echo "Note: This step requires an AWS account with IAM administrative privileges."
echo "If you encounter permission errors, please run the update_iam_permissions.sh script separately with appropriate credentials."
./update_iam_permissions.sh

# Start the services
echo "Starting genomics treatment services..."
python start_services.py