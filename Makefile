.PHONY: help setup test clean run lint format verify docs

# Default target
help:
	@echo "Available commands:"
	@echo "  setup    - Set up development environment"
	@echo "  test     - Run tests"
	@echo "  clean    - Clean up temporary files"
	@echo "  run      - Run the system"
	@echo "  lint     - Run code linting"
	@echo "  format   - Format code"
	@echo "  verify   - Verify system setup"
	@echo "  docs     - Generate documentation"

# Set up development environment
setup:
	@echo "Setting up development environment..."
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	python verify_setup.py

# Run tests
test:
	@echo "Running tests..."
	python -m pytest tests/ -v --cov=services

# Clean up temporary files
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".coverage" -exec rm -r {} +
	find . -type d -name "htmlcov" -exec rm -r {} +
	find . -type f -name ".DS_Store" -delete

# Run the system
run:
	@echo "Starting the system..."
	python run_system.py

# Run code linting
lint:
	@echo "Running linters..."
	flake8 services/ tests/
	pylint services/ tests/
	mypy services/ tests/

# Format code
format:
	@echo "Formatting code..."
	black services/ tests/
	isort services/ tests/

# Verify system setup
verify:
	@echo "Verifying system setup..."
	python verify_setup.py

# Generate documentation
docs:
	@echo "Generating documentation..."
	mkdocs build

# Kill all running services
kill:
	@echo "Killing all services..."
	pkill -f "python -m services" || true
	pkill -f "DynamoDBLocal" || true

# Start DynamoDB Local
dynamodb:
	@echo "Starting DynamoDB Local..."
	java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb

# Create database tables
createdb:
	@echo "Creating database tables..."
	python verify_dynamodb.py

# Run specific service
.PHONY: run-service
run-service:
	@if [ "$(service)" = "" ]; then \
		echo "Please specify a service: make run-service service=<service_name>"; \
		exit 1; \
	fi
	@echo "Running $(service) service..."
	python -m services.$(service).main

# Development setup with pre-commit hooks
dev-setup: setup
	@echo "Setting up pre-commit hooks..."
	pre-commit install

# Run security checks
security:
	@echo "Running security checks..."
	bandit -r services/ -ll
	safety check

# Check dependencies for updates
deps-check:
	@echo "Checking for dependency updates..."
	pip list --outdated

# Update dependencies
deps-update:
	@echo "Updating dependencies..."
	pip install --upgrade -r requirements.txt

# Run system tests
system-test:
	@echo "Running system tests..."
	python -m tests.system_test

# Run integration tests
integration-test:
	@echo "Running integration tests..."
	python -m pytest tests/integration -v

# Run unit tests
unit-test:
	@echo "Running unit tests..."
	python -m pytest tests/unit -v

# Generate test coverage report
coverage:
	@echo "Generating test coverage report..."
	coverage run -m pytest tests/
	coverage report
	coverage html

# Start all services in development mode
dev:
	@echo "Starting services in development mode..."
	python start_services.py --dev

# Create a new service
create-service:
	@if [ "$(name)" = "" ]; then \
		echo "Please specify a service name: make create-service name=<service_name>"; \
		exit 1; \
	fi
	@echo "Creating new service: $(name)"
	mkdir -p services/$(name)
	touch services/$(name)/__init__.py
	touch services/$(name)/main.py
	@echo "Service $(name) created"
