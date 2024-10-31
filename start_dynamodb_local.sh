#!/bin/bash

# Exit on error
set -e

# Function to print messages
print_message() {
    echo "===> $1"
}

# Function to check if Java is installed
check_java() {
    if ! command -v java &> /dev/null; then
        print_message "Error: Java is required but not installed."
        exit 1
    fi
}

# Function to download DynamoDB Local if not present
download_dynamodb() {
    if [ ! -f "DynamoDBLocal.jar" ]; then
        print_message "Downloading DynamoDB Local..."
        curl -O https://s3.us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.tar.gz
        tar xzf dynamodb_local_latest.tar.gz
        rm dynamodb_local_latest.tar.gz
    fi
}

# Function to check if DynamoDB is already running
check_dynamodb_running() {
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        print_message "DynamoDB is already running on port 8000"
        return 0
    fi
    return 1
}

# Function to create required tables
create_tables() {
    print_message "Creating required tables..."
    python verify_dynamodb.py
}

# Main execution
main() {
    print_message "Starting DynamoDB Local setup..."
    
    # Check requirements
    check_java
    
    # Check if DynamoDB is already running
    if check_dynamodb_running; then
        print_message "Using existing DynamoDB instance"
    else
        # Download DynamoDB if needed
        download_dynamodb
        
        # Create data directory if it doesn't exist
        mkdir -p data
        
        # Start DynamoDB Local
        print_message "Starting DynamoDB Local..."
        java -Djava.library.path=./DynamoDBLocal_lib \
             -jar DynamoDBLocal.jar \
             -dbPath ./data \
             -sharedDb &
        
        # Wait for DynamoDB to start
        print_message "Waiting for DynamoDB to start..."
        sleep 5
    fi
    
    # Create tables
    create_tables
    
    print_message "DynamoDB Local setup completed successfully!"
    print_message "DynamoDB is running on http://localhost:8000"
}

# Run main function
main
