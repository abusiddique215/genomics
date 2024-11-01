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

# Function to install Python 3.9 if needed
install_python39() {
    if ! command -v python3.9 &> /dev/null; then
        print_message "Installing Python 3.9..."
        case "$(uname -s)" in
            Darwin*)    # macOS
                brew install python@3.9
                ;;
            Linux*)     # Linux
                if command -v apt-get &> /dev/null; then
                    # Ubuntu/Debian
                    sudo apt-get update
                    sudo apt-get install -y python3.9 python3.9-venv python3.9-dev
                elif command -v yum &> /dev/null; then
                    # CentOS/RHEL
                    sudo yum install -y python39 python39-devel
                fi
                ;;
            *)
                print_message "Please install Python 3.9 manually for your operating system"
                exit 1
                ;;
        esac
    fi
}

# Function to install Poetry
install_poetry() {
    if ! command -v poetry &> /dev/null; then
        print_message "Installing Poetry..."
        curl -sSL https://install.python-poetry.org | python3 -
    fi
}

# Function to set up git hooks
setup_git_hooks() {
    print_message "Setting up git hooks..."
    
    # Create pre-commit hook
    mkdir -p .git/hooks
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

# Run tests
poetry run pytest tests/ -m "not slow" || exit 1

# Run linting
poetry run black . --check || exit 1
poetry run flake8 . || exit 1
poetry run mypy . || exit 1

# Run security checks
poetry run bandit -r services/ || exit 1
poetry run safety check || exit 1
EOF
    
    chmod +x .git/hooks/pre-commit
    
    # Create pre-push hook
    cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash

# Run all tests
poetry run pytest tests/ || exit 1

# Run security audit
poetry run safety check || exit 1
EOF
    
    chmod +x .git/hooks/pre-push
}

# Function to set up environment variables
setup_env() {
    print_message "Setting up environment variables..."
    if [ ! -f .env ]; then
        cp .env.example .env
        print_message "Please update .env with your configuration"
    fi
}

# Function to set up AWS credentials
setup_aws() {
    print_message "Setting up AWS credentials..."
    mkdir -p ~/.aws
    
    if [ ! -f ~/.aws/credentials ]; then
        cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = your_access_key
aws_secret_access_key = your_secret_key
EOF
        print_message "Please update ~/.aws/credentials with your AWS credentials"
    fi
    
    if [ ! -f ~/.aws/config ]; then
        cat > ~/.aws/config << EOF
[default]
region = us-west-2
output = json
EOF
        print_message "Please update ~/.aws/config with your preferred region"
    fi
}

# Function to create necessary directories
create_directories() {
    print_message "Creating necessary directories..."
    mkdir -p data
    mkdir -p logs
    mkdir -p models
    mkdir -p tests/data
    
    # Create .gitkeep files
    touch data/.gitkeep
    touch logs/.gitkeep
    touch models/.gitkeep
    touch tests/data/.gitkeep
}

# Function to generate test data
generate_test_data() {
    print_message "Generating test data..."
    poetry run python generate_mock_patients.py --count 100 --output data/test_patients.json --treatment-history --pretty
}

# Function to verify setup
verify_setup() {
    print_message "Verifying setup..."
    poetry run python verify_environment.py
}

# Main execution
main() {
    print_message "Starting project initialization..."
    
    # Check and install requirements
    check_command curl
    install_python39
    install_poetry
    
    # Set up Poetry environment
    print_message "Setting up Poetry environment..."
    poetry env use python3.9
    poetry install
    
    # Set up project structure
    create_directories
    setup_env
    setup_aws
    setup_git_hooks
    
    # Generate initial data
    generate_test_data
    
    # Verify setup
    verify_setup
    
    print_message "Project initialization completed!"
    print_message "Next steps:"
    print_message "1. Update .env with your configuration"
    print_message "2. Update AWS credentials in ~/.aws/credentials"
    print_message "3. Start development with: poetry shell"
}

# Run main function
main
