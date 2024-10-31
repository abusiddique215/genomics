#!/bin/bash

# Exit on error
set -e

# Function to display usage
usage() {
    echo "Usage: $0 [command]"
    echo "Commands:"
    echo "  start       - Start all services"
    echo "  stop        - Stop all services"
    echo "  restart     - Restart all services"
    echo "  build       - Build all services"
    echo "  logs        - Show logs from all services"
    echo "  status      - Show status of all services"
    echo "  clean       - Remove all containers and images"
    echo "  test        - Run tests in containers"
    exit 1
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "Error: Docker is not running"
        exit 1
    fi
}

# Start services
start() {
    echo "Starting services..."
    docker-compose up -d
    echo "Services started. Use '$0 logs' to view logs"
}

# Stop services
stop() {
    echo "Stopping services..."
    docker-compose down
}

# Restart services
restart() {
    echo "Restarting services..."
    docker-compose restart
}

# Build services
build() {
    echo "Building services..."
    docker-compose build --no-cache
}

# Show logs
logs() {
    docker-compose logs -f
}

# Show status
status() {
    docker-compose ps
}

# Clean up
clean() {
    echo "Cleaning up Docker resources..."
    docker-compose down -v --rmi all --remove-orphans
}

# Run tests
test() {
    echo "Running tests in containers..."
    docker-compose run --rm patient-management python -m pytest tests/
}

# Check if Docker is running
check_docker

# Parse command
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    build)
        build
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    clean)
        clean
        ;;
    test)
        test
        ;;
    *)
        usage
        ;;
esac
