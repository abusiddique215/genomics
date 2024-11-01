#!/bin/bash

# Exit on error
set -e

# Function to print messages
print_message() {
    echo "===> $1"
}

# Function to check AWS CLI
check_aws() {
    if ! command -v aws &> /dev/null; then
        print_message "Error: AWS CLI is required but not installed."
        print_message "Install it from: https://aws.amazon.com/cli/"
        exit 1
    fi
}

# Function to check AWS credentials
check_credentials() {
    if ! aws sts get-caller-identity &> /dev/null; then
        print_message "Error: AWS credentials not configured or invalid."
        print_message "Configure with: aws configure"
        exit 1
    fi
}

# Function to deploy to AWS
deploy() {
    local environment=$1
    if [ -z "$environment" ]; then
        environment="dev"
    fi
    
    print_message "Deploying to $environment environment..."
    
    # Package application
    print_message "Packaging application..."
    aws cloudformation package \
        --template-file template.yaml \
        --s3-bucket genomics-deployment-$environment \
        --output-template-file packaged.yaml
    
    # Deploy application
    print_message "Deploying application..."
    aws cloudformation deploy \
        --template-file packaged.yaml \
        --stack-name genomics-$environment \
        --capabilities CAPABILITY_IAM \
        --parameter-overrides \
            Environment=$environment \
            DynamoDBTableName=patients-$environment
}

# Function to create DynamoDB tables
create_tables() {
    local environment=$1
    if [ -z "$environment" ]; then
        environment="dev"
    fi
    
    print_message "Creating DynamoDB tables for $environment environment..."
    
    # Create patients table
    aws dynamodb create-table \
        --table-name patients-$environment \
        --attribute-definitions \
            AttributeName=id,AttributeType=S \
        --key-schema \
            AttributeName=id,KeyType=HASH \
        --provisioned-throughput \
            ReadCapacityUnits=5,WriteCapacityUnits=5 \
        --tags Key=Environment,Value=$environment || true
    
    # Create patient progress table
    aws dynamodb create-table \
        --table-name patient-progress-$environment \
        --attribute-definitions \
            AttributeName=patient_id,AttributeType=S \
            AttributeName=timestamp,AttributeType=S \
        --key-schema \
            AttributeName=patient_id,KeyType=HASH \
            AttributeName=timestamp,KeyType=RANGE \
        --provisioned-throughput \
            ReadCapacityUnits=5,WriteCapacityUnits=5 \
        --tags Key=Environment,Value=$environment || true
}

# Function to delete DynamoDB tables
delete_tables() {
    local environment=$1
    if [ -z "$environment" ]; then
        environment="dev"
    fi
    
    print_message "Deleting DynamoDB tables for $environment environment..."
    
    aws dynamodb delete-table --table-name patients-$environment || true
    aws dynamodb delete-table --table-name patient-progress-$environment || true
}

# Function to create S3 bucket
create_bucket() {
    local environment=$1
    if [ -z "$environment" ]; then
        environment="dev"
    fi
    
    print_message "Creating S3 bucket for $environment environment..."
    
    aws s3 mb s3://genomics-deployment-$environment \
        --region $(aws configure get region) || true
}

# Function to delete S3 bucket
delete_bucket() {
    local environment=$1
    if [ -z "$environment" ]; then
        environment="dev"
    fi
    
    print_message "Deleting S3 bucket for $environment environment..."
    
    aws s3 rb s3://genomics-deployment-$environment --force || true
}

# Function to create IAM roles
create_roles() {
    print_message "Creating IAM roles..."
    
    # Create service role
    aws iam create-role \
        --role-name GenomicsServiceRole \
        --assume-role-policy-document file://elasticbeanstalk-policy.json || true
    
    # Attach policies
    aws iam attach-role-policy \
        --role-name GenomicsServiceRole \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole || true
    
    aws iam attach-role-policy \
        --role-name GenomicsServiceRole \
        --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess || true
}

# Function to delete IAM roles
delete_roles() {
    print_message "Deleting IAM roles..."
    
    # Detach policies
    aws iam detach-role-policy \
        --role-name GenomicsServiceRole \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole || true
    
    aws iam detach-role-policy \
        --role-name GenomicsServiceRole \
        --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess || true
    
    # Delete role
    aws iam delete-role --role-name GenomicsServiceRole || true
}

# Function to show stack status
show_status() {
    local environment=$1
    if [ -z "$environment" ]; then
        environment="dev"
    fi
    
    print_message "Stack status for $environment environment:"
    aws cloudformation describe-stacks \
        --stack-name genomics-$environment \
        --query 'Stacks[0].StackStatus' \
        --output text || echo "Stack not found"
}

# Function to show help
show_help() {
    echo "AWS resource management script"
    echo
    echo "Usage: $0 [command] [environment]"
    echo
    echo "Commands:"
    echo "  deploy      - Deploy application"
    echo "  create-db   - Create DynamoDB tables"
    echo "  delete-db   - Delete DynamoDB tables"
    echo "  create-s3   - Create S3 bucket"
    echo "  delete-s3   - Delete S3 bucket"
    echo "  create-iam  - Create IAM roles"
    echo "  delete-iam  - Delete IAM roles"
    echo "  status      - Show stack status"
    echo "  setup       - Set up all resources"
    echo "  teardown    - Delete all resources"
    echo "  help        - Show this help message"
    echo
    echo "Environments:"
    echo "  dev         - Development environment (default)"
    echo "  staging     - Staging environment"
    echo "  prod        - Production environment"
}

# Function to set up all resources
setup_all() {
    local environment=$1
    if [ -z "$environment" ]; then
        environment="dev"
    fi
    
    create_bucket "$environment"
    create_tables "$environment"
    create_roles
    deploy "$environment"
}

# Function to tear down all resources
teardown_all() {
    local environment=$1
    if [ -z "$environment" ]; then
        environment="dev"
    fi
    
    delete_bucket "$environment"
    delete_tables "$environment"
    delete_roles
    
    # Delete CloudFormation stack
    aws cloudformation delete-stack --stack-name genomics-$environment || true
}

# Check requirements
check_aws
check_credentials

# Main execution
case "$1" in
    "deploy")
        deploy "$2"
        ;;
    "create-db")
        create_tables "$2"
        ;;
    "delete-db")
        delete_tables "$2"
        ;;
    "create-s3")
        create_bucket "$2"
        ;;
    "delete-s3")
        delete_bucket "$2"
        ;;
    "create-iam")
        create_roles
        ;;
    "delete-iam")
        delete_roles
        ;;
    "status")
        show_status "$2"
        ;;
    "setup")
        setup_all "$2"
        ;;
    "teardown")
        teardown_all "$2"
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
