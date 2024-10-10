#!/bin/bash

# Check if the user has sufficient permissions
if ! aws iam get-user &> /dev/null; then
    echo "Error: Insufficient permissions to manage IAM users and policies."
    echo "Please run this script with an AWS account that has IAM administrative privileges."
    exit 1
fi

# Create the policy document
cat << EOF > genomics_api_policy.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams",
                "s3:*",
                "dynamodb:*"
            ],
            "Resource": "*"
        }
    ]
}
EOF

# Get the AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Check if the policy already exists
EXISTING_POLICY=$(aws iam list-policies --query "Policies[?PolicyName=='GenomicsAPIPolicy'].Arn" --output text)

if [ -z "$EXISTING_POLICY" ]; then
    # Create the IAM policy
    POLICY_ARN=$(aws iam create-policy --policy-name GenomicsAPIPolicy --policy-document file://genomics_api_policy.json --query Policy.Arn --output text)
    echo "Created new policy: $POLICY_ARN"
else
    POLICY_ARN=$EXISTING_POLICY
    echo "Using existing policy: $POLICY_ARN"
fi

# Attach the policy to the user
aws iam attach-user-policy --user-name genomics-api-user --policy-arn $POLICY_ARN

# Clean up
rm genomics_api_policy.json

echo "IAM permissions updated for genomics-api-user"