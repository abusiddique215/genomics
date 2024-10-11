#!/bin/bash

# Check if the user has sufficient permissions
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: Unable to get AWS identity. Please check your AWS credentials."
    exit 1
fi

# Get the current user's ARN
USER_ARN=$(aws sts get-caller-identity --query Arn --output text)
echo "Current user ARN: $USER_ARN"

# Check if the user can list roles
if aws iam list-roles --max-items 1 &> /dev/null; then
    echo "User has permission to list IAM roles."
else
    echo "User does not have permission to list IAM roles."
fi

# Check if the user can assume the GenomicsAPIRole
ROLE_NAME="GenomicsAPIRole"
if aws sts assume-role --role-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/$ROLE_NAME" --role-session-name test-session &> /dev/null; then
    echo "User can assume the $ROLE_NAME role."
else
    echo "User cannot assume the $ROLE_NAME role."
fi

echo "
Based on the checks above, please ensure the following manual steps are completed by an AWS administrator:

1. Create an IAM role named 'GenomicsAPIRole' if it doesn't exist.
2. Attach the necessary policies to the 'GenomicsAPIRole' for accessing required AWS services (S3, DynamoDB, etc.).
3. Update the trust relationship of 'GenomicsAPIRole' to allow the genomics-api-user to assume it:

{
  \"Version\": \"2012-10-17\",
  \"Statement\": [
    {
      \"Effect\": \"Allow\",
      \"Principal\": {
        \"AWS\": \"$USER_ARN\"
      },
      \"Action\": \"sts:AssumeRole\"
    }
  ]
}

4. Grant the genomics-api-user permission to assume the 'GenomicsAPIRole' by attaching this policy:

{
    \"Version\": \"2012-10-17\",
    \"Statement\": [
        {
            \"Effect\": \"Allow\",
            \"Action\": \"sts:AssumeRole\",
            \"Resource\": \"arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/$ROLE_NAME\"
        }
    ]
}

After these steps are completed, run this script again to verify the permissions.
"

echo "IAM permission check completed. Please review the output and take necessary actions."