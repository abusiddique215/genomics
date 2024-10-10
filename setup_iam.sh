#!/bin/bash

# This script should be run by an AWS administrator to set up the initial IAM user and permissions

# Check if the user has sufficient permissions
if ! aws iam get-user &> /dev/null; then
    echo "Error: Insufficient permissions to manage IAM users and policies."
    echo "Please run this script with an AWS account that has IAM administrative privileges."
    exit 1
fi

# Create the genomics-api-user if it doesn't exist
if ! aws iam get-user --user-name genomics-api-user &> /dev/null; then
    echo "Creating genomics-api-user..."
    aws iam create-user --user-name genomics-api-user
    aws iam create-access-key --user-name genomics-api-user > access_key.json
    echo "Access key created. Please update your .env file with the following:"
    echo "AWS_ACCESS_KEY_ID=$(jq -r .AccessKey.AccessKeyId access_key.json)"
    echo "AWS_SECRET_ACCESS_KEY=$(jq -r .AccessKey.SecretAccessKey access_key.json)"
    rm access_key.json
else
    echo "genomics-api-user already exists."
fi

# Run the update_iam_permissions.sh script
./update_iam_permissions.sh

echo "IAM setup completed."