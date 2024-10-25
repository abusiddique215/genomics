#!/bin/bash

# Download DynamoDB Local if not already present
if [ ! -f "dynamodb_local_latest.tar.gz" ]; then
    echo "Downloading DynamoDB Local..."
    curl -O https://s3.us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.tar.gz
    tar xzf dynamodb_local_latest.tar.gz
fi

# Start DynamoDB Local
echo "Starting DynamoDB Local..."
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb
