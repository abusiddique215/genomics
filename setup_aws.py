#!/usr/bin/env python3

import boto3
import json
import logging
import os
import sys
from botocore.exceptions import ClientError
from typing import List, Dict, Any
from config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AWSResourceManager:
    """Manage AWS resources for the genomics system"""
    
    def __init__(self):
        self.region = config.get('database.region', 'us-west-2')
        self.endpoint_url = config.get('database.endpoint')
        
        # Initialize AWS clients
        self.dynamodb = boto3.client(
            'dynamodb',
            region_name=self.region,
            endpoint_url=self.endpoint_url
        )
        self.iam = boto3.client('iam', region_name=self.region)
    
    def create_tables(self):
        """Create required DynamoDB tables"""
        tables = [
            {
                'TableName': 'patients',
                'KeySchema': [
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                'AttributeDefinitions': [
                    {'AttributeName': 'id', 'AttributeType': 'S'}
                ],
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            },
            {
                'TableName': 'patient_progress',
                'KeySchema': [
                    {'AttributeName': 'patient_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                'AttributeDefinitions': [
                    {'AttributeName': 'patient_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            },
            {
                'TableName': 'treatment_history',
                'KeySchema': [
                    {'AttributeName': 'patient_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'treatment_id', 'KeyType': 'RANGE'}
                ],
                'AttributeDefinitions': [
                    {'AttributeName': 'patient_id', 'AttributeType': 'S'},
                    {'AttributeName': 'treatment_id', 'AttributeType': 'S'}
                ],
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            }
        ]
        
        for table in tables:
            try:
                self.dynamodb.create_table(**table)
                logger.info(f"Created table {table['TableName']}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceInUseException':
                    logger.info(f"Table {table['TableName']} already exists")
                else:
                    logger.error(f"Error creating table {table['TableName']}: {str(e)}")
                    raise
    
    def setup_iam_role(self):
        """Set up IAM role for the application"""
        role_name = 'GenomicsServiceRole'
        
        # Create role
        try:
            role = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps({
                    'Version': '2012-10-17',
                    'Statement': [{
                        'Effect': 'Allow',
                        'Principal': {
                            'Service': 'lambda.amazonaws.com'
                        },
                        'Action': 'sts:AssumeRole'
                    }]
                })
            )
            logger.info(f"Created IAM role {role_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                logger.info(f"IAM role {role_name} already exists")
            else:
                logger.error(f"Error creating IAM role: {str(e)}")
                raise
        
        # Attach policies
        policies = [
            'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
            'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess'
        ]
        
        for policy in policies:
            try:
                self.iam.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy
                )
                logger.info(f"Attached policy {policy} to role {role_name}")
            except ClientError as e:
                logger.error(f"Error attaching policy {policy}: {str(e)}")
                raise
    
    def verify_setup(self) -> bool:
        """Verify AWS setup"""
        try:
            # Check DynamoDB tables
            tables = self.dynamodb.list_tables()['TableNames']
            required_tables = ['patients', 'patient_progress', 'treatment_history']
            
            for table in required_tables:
                if table not in tables:
                    logger.error(f"Missing required table: {table}")
                    return False
                
                # Check table status
                response = self.dynamodb.describe_table(TableName=table)
                if response['Table']['TableStatus'] != 'ACTIVE':
                    logger.error(f"Table {table} is not active")
                    return False
            
            # Check IAM role
            try:
                self.iam.get_role(RoleName='GenomicsServiceRole')
            except ClientError:
                logger.error("Missing required IAM role")
                return False
            
            logger.info("AWS setup verification completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying setup: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up AWS resources"""
        # Delete tables
        tables = ['patients', 'patient_progress', 'treatment_history']
        for table in tables:
            try:
                self.dynamodb.delete_table(TableName=table)
                logger.info(f"Deleted table {table}")
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    logger.error(f"Error deleting table {table}: {str(e)}")
        
        # Clean up IAM role
        role_name = 'GenomicsServiceRole'
        try:
            # Detach policies
            policies = self.iam.list_attached_role_policies(RoleName=role_name)
            for policy in policies['AttachedPolicies']:
                self.iam.detach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy['PolicyArn']
                )
            
            # Delete role
            self.iam.delete_role(RoleName=role_name)
            logger.info(f"Deleted IAM role {role_name}")
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchEntity':
                logger.error(f"Error cleaning up IAM role: {str(e)}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Set up AWS resources')
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Clean up AWS resources'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify AWS setup'
    )
    
    args = parser.parse_args()
    manager = AWSResourceManager()
    
    try:
        if args.cleanup:
            manager.cleanup()
        elif args.verify:
            if not manager.verify_setup():
                sys.exit(1)
        else:
            manager.create_tables()
            manager.setup_iam_role()
            if not manager.verify_setup():
                sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
