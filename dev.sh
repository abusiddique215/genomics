#!/bin/bash

# Exit on error
set -e

# Function to print messages
print_message() {
    echo "===> $1"
}

# Function to show help
show_help() {
    echo "Development workflow management script"
    echo
    echo "Usage: $0 [command]"
    echo
    echo "Commands:"
    echo "  setup       - Set up development environment"
    echo "  start       - Start all services"
    echo "  stop        - Stop all services"
    echo "  restart     - Restart all services"
    echo "  test        - Run tests"
    echo "  lint        - Run linting"
    echo "  format      - Format code"
    echo "  check       - Run all checks"
    echo "  clean       - Clean up temporary files"
    echo "  docs        - Generate documentation"
    echo "  db          - Start DynamoDB Local"
    echo "  mock        - Generate mock data"
    echo "  update      - Update dependencies"
    echo "  docker      - Manage Docker services"
    echo "  logs        - View service logs"
    echo "  shell       - Start Poetry shell"
    echo "  help        - Show this help message"
    echo
    echo "Options:"
    echo "  --dev       - Run in development mode"
    echo "  --prod      - Run in production mode"
    echo "  --coverage  - Run tests with coverage"
}

# Function to run tests
run_tests() {
    print_message "Running tests..."
    
    if [ "$1" == "--coverage" ]; then
        poetry run pytest tests/ --cov=services --cov-report=html
        print_message "Coverage report generated in htmlcov/"
    else
        poetry run pytest tests/ "$@"
    fi
}

# Function to run linting
run_lint() {
    print_message "Running linting..."
    poetry run black . --check
    poetry run flake8 .
    poetry run mypy .
    poetry run bandit -r services/
    poetry run safety check
}

# Function to format code
format_code() {
    print_message "Formatting code..."
    poetry run black .
    poetry run isort .
}

# Function to clean up
clean_up() {
    print_message "Cleaning up..."
    find . -type d -name "__pycache__" -exec rm -r {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.pyd" -delete
    find . -type d -name "*.egg-info" -exec rm -r {} +
    find . -type d -name ".pytest_cache" -exec rm -r {} +
    find . -type d -name ".coverage" -exec rm -r {} +
    find . -type d -name "htmlcov" -exec rm -r {} +
    find . -type f -name ".DS_Store" -delete
}

# Function to generate documentation
generate_docs() {
    print_message "Generating documentation..."
    poetry run mkdocs build
    print_message "Documentation generated in site/"
}

# Function to start services
start_services() {
    print_message "Starting services..."
    if [ "$1" == "--dev" ]; then
        ./start_genomics_project.sh dev
    else
        ./start_genomics_project.sh start
    fi
}

# Function to stop services
stop_services() {
    print_message "Stopping services..."
    ./start_genomics_project.sh stop
}

# Function to manage Docker services
manage_docker() {
    case "$1" in
        "build")
            print_message "Building Docker images..."
            docker-compose build
            ;;
        "up")
            print_message "Starting Docker services..."
            docker-compose up -d
            ;;
        "down")
            print_message "Stopping Docker services..."
            docker-compose down
            ;;
        "logs")
            print_message "Showing Docker logs..."
            docker-compose logs -f
            ;;
        *)
            print_message "Invalid Docker command"
            exit 1
            ;;
    esac
}

# Function to view logs
view_logs() {
    if [ -z "$1" ]; then
        print_message "Please specify a service name"
        exit 1
    fi
    
    log_file="logs/$1.log"
    if [ -f "$log_file" ]; then
        tail -f "$log_file"
    else
        print_message "Log file not found: $log_file"
        exit 1
    fi
}

# Function to update dependencies
update_deps() {
    print_message "Updating dependencies..."
    poetry update
    poetry install
    poetry run pip list --outdated
}

# Function to run all checks
run_checks() {
    print_message "Running all checks..."
    run_lint
    run_tests
    poetry run python verify_environment.py
}

# Main execution
case "$1" in
    "setup")
        ./init_project.sh
        ;;
    "start")
        start_services "$2"
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        start_services "$2"
        ;;
    "test")
        shift
        run_tests "$@"
        ;;
    "lint")
        run_lint
        ;;
    "format")
        format_code
        ;;
    "check")
        run_checks
        ;;
    "clean")
        clean_up
        ;;
    "docs")
        generate_docs
        ;;
    "db")
        ./start_dynamodb_local.sh
        ;;
    "mock")
        poetry run python generate_mock_patients.py "$@"
        ;;
    "update")
        update_deps
        ;;
    "docker")
        shift
        manage_docker "$@"
        ;;
    "logs")
        shift
        view_logs "$@"
        ;;
    "shell")
        poetry shell
        ;;
    "help"|"")
        show_help
        ;;
    *)
        print_message "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
