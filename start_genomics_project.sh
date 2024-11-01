#!/bin/bash

# Exit on error
set -e

# Function to print messages
print_message() {
    echo "===> $1"
}

# Function to check if a command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_message "Error: $1 is required but not installed."
        exit 1
    fi
}

# Function to start DynamoDB
start_dynamodb() {
    print_message "Starting DynamoDB..."
    ./start_dynamodb_local.sh
}

# Function to verify AWS setup
verify_aws() {
    print_message "Verifying AWS setup..."
    python setup_aws.py --verify
}

# Function to generate test data
generate_test_data() {
    print_message "Generating test data..."
    python generate_mock_patients.py --count 100 --output data/test_patients.json --treatment-history --pretty
}

# Function to start services
start_services() {
    print_message "Starting services..."
    python start_services.py "$@"
}

# Function to verify services
verify_services() {
    print_message "Verifying services..."
    python verify_services.py
}

# Function to show status
show_status() {
    print_message "System Status"
    echo "DynamoDB: $(curl -s http://localhost:8000 > /dev/null && echo "Running" || echo "Stopped")"
    echo "Patient Management: $(curl -s http://localhost:8080/health > /dev/null && echo "Healthy" || echo "Unhealthy")"
    echo "Treatment Prediction: $(curl -s http://localhost:8083/health > /dev/null && echo "Healthy" || echo "Unhealthy")"
    echo "Data Ingestion: $(curl -s http://localhost:8084/health > /dev/null && echo "Healthy" || echo "Unhealthy")"
}

# Function to clean up
cleanup() {
    print_message "Cleaning up..."
    pkill -f "DynamoDBLocal" || true
    pkill -f "uvicorn" || true
    print_message "Cleanup complete"
}

# Function to show help
show_help() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  start       Start the system"
    echo "  stop        Stop the system"
    echo "  restart     Restart the system"
    echo "  status      Show system status"
    echo "  setup       Set up the system"
    echo "  clean       Clean up resources"
    echo "  test        Run tests"
    echo "  dev         Start in development mode"
    echo "  help        Show this help message"
}

# Function to run tests
run_tests() {
    print_message "Running tests..."
    pytest tests/ -v
}

# Function to set up the system
setup_system() {
    print_message "Setting up the system..."
    
    # Check requirements
    check_command python3
    check_command pip
    check_command java
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_message "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    print_message "Installing dependencies..."
    pip install -r requirements.txt
    
    # Set up AWS resources
    print_message "Setting up AWS resources..."
    python setup_aws.py
    
    # Create necessary directories
    mkdir -p data
    mkdir -p logs
    mkdir -p models
    
    # Generate test data
    generate_test_data
    
    print_message "Setup complete!"
}

# Trap cleanup on exit
trap cleanup EXIT

# Main execution
case "$1" in
    start)
        start_dynamodb
        start_services "${@:2}"
        verify_services
        show_status
        ;;
    stop)
        cleanup
        ;;
    restart)
        cleanup
        start_dynamodb
        start_services "${@:2}"
        verify_services
        show_status
        ;;
    status)
        show_status
        ;;
    setup)
        setup_system
        ;;
    clean)
        cleanup
        ;;
    test)
        run_tests
        ;;
    dev)
        start_dynamodb
        start_services --dev
        verify_services
        show_status
        ;;
    help)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac
