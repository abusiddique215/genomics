#!/usr/bin/env python3

import boto3
import logging
import json
from botocore.exceptions import ClientError
from typing import Dict, Any, List
import time
from config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DynamoDBVerifier:
    """Verify DynamoDB setup and functionality"""
    
    def __init__(self):
        self.endpoint_url = config.get('database.endpoint')
        self.region = config.get('database.region', 'us-west-2')
        
        self.dynamodb = boto3.client(
            'dynamodb',
            endpoint_url=self.endpoint_url,
            region_name=self.region
        )
    
    def verify_table_exists(self, table_name: str) -> bool:
        """Verify a table exists and is active"""
        try:
            response = self.dynamodb.describe_table(TableName=table_name)
            return response['Table']['TableStatus'] == 'ACTIVE'
        except ClientError:
            return False
    
    def verify_crud_operations(self, table_name: str) -> bool:
        """Verify CRUD operations on a table"""
        test_item = {
            'id': {'S': 'TEST_ID'},
            'data': {'S': json.dumps({'test': 'data'})}
        }
        
        try:
            # Create
            self.dynamodb.put_item(
                TableName=table_name,
                Item=test_item
            )
            
            # Read
            response = self.dynamodb.get_item(
                TableName=table_name,
                Key={'id': {'S': 'TEST_ID'}}
            )
            if 'Item' not in response:
                return False
            
            # Update
            self.dynamodb.update_item(
                TableName=table_name,
                Key={'id': {'S': 'TEST_ID'}},
                UpdateExpression='SET #data = :data',
                ExpressionAttributeNames={'#data': 'data'},
                ExpressionAttributeValues={
                    ':data': {'S': json.dumps({'test': 'updated'})}
                }
            )
            
            # Delete
            self.dynamodb.delete_item(
                TableName=table_name,
                Key={'id': {'S': 'TEST_ID'}}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"CRUD operations failed: {str(e)}")
            return False
    
    def verify_table_throughput(self, table_name: str) -> bool:
        """Verify table throughput settings"""
        try:
            response = self.dynamodb.describe_table(TableName=table_name)
            throughput = response['Table']['ProvisionedThroughput']
            
            return (
                throughput['ReadCapacityUnits'] > 0 and
                throughput['WriteCapacityUnits'] > 0
            )
        except Exception as e:
            logger.error(f"Throughput verification failed: {str(e)}")
            return False
    
    def verify_batch_operations(self, table_name: str) -> bool:
        """Verify batch operations"""
        try:
            # Batch write
            items = [
                {
                    'id': {'S': f'BATCH_TEST_{i}'},
                    'data': {'S': json.dumps({'batch': i})}
                }
                for i in range(5)
            ]
            
            self.dynamodb.batch_write_item(
                RequestItems={
                    table_name: [
                        {'PutRequest': {'Item': item}}
                        for item in items
                    ]
                }
            )
            
            # Batch get
            response = self.dynamodb.batch_get_item(
                RequestItems={
                    table_name: {
                        'Keys': [
                            {'id': {'S': f'BATCH_TEST_{i}'}}
                            for i in range(5)
                        ]
                    }
                }
            )
            
            # Clean up
            self.dynamodb.batch_write_item(
                RequestItems={
                    table_name: [
                        {'DeleteRequest': {'Key': {'id': {'S': f'BATCH_TEST_{i}'}}}}
                        for i in range(5)
                    ]
                }
            )
            
            return len(response['Responses'][table_name]) == 5
            
        except Exception as e:
            logger.error(f"Batch operations failed: {str(e)}")
            return False
    
    def verify_queries(self, table_name: str) -> bool:
        """Verify query operations"""
        try:
            # Only verify if table has a sort key
            response = self.dynamodb.describe_table(TableName=table_name)
            if len(response['Table']['KeySchema']) > 1:
                # Add test items
                items = [
                    {
                        'patient_id': {'S': 'TEST_PATIENT'},
                        'timestamp': {'S': f'2023-01-{i:02d}'},
                        'data': {'S': json.dumps({'day': i})}
                    }
                    for i in range(1, 6)
                ]
                
                for item in items:
                    self.dynamodb.put_item(TableName=table_name, Item=item)
                
                # Query items
                response = self.dynamodb.query(
                    TableName=table_name,
                    KeyConditionExpression='patient_id = :pid',
                    ExpressionAttributeValues={
                        ':pid': {'S': 'TEST_PATIENT'}
                    }
                )
                
                # Clean up
                for item in items:
                    self.dynamodb.delete_item(
                        TableName=table_name,
                        Key={
                            'patient_id': item['patient_id'],
                            'timestamp': item['timestamp']
                        }
                    )
                
                return len(response['Items']) == 5
            
            return True
            
        except Exception as e:
            logger.error(f"Query operations failed: {str(e)}")
            return False
    
    def run_all_verifications(self) -> bool:
        """Run all verifications"""
        tables = ['patients', 'patient_progress', 'treatment_history']
        all_passed = True
        
        for table in tables:
            logger.info(f"Verifying table: {table}")
            
            if not self.verify_table_exists(table):
                logger.error(f"Table {table} does not exist or is not active")
                all_passed = False
                continue
            
            verifications = [
                (self.verify_crud_operations, "CRUD operations"),
                (self.verify_table_throughput, "Throughput settings"),
                (self.verify_batch_operations, "Batch operations"),
                (self.verify_queries, "Query operations")
            ]
            
            for verify_func, name in verifications:
                if not verify_func(table):
                    logger.error(f"{name} verification failed for table {table}")
                    all_passed = False
                else:
                    logger.info(f"{name} verification passed for table {table}")
        
        return all_passed

def main():
    """Main function"""
    verifier = DynamoDBVerifier()
    if not verifier.run_all_verifications():
        logger.error("DynamoDB verification failed")
        exit(1)
    logger.info("DynamoDB verification completed successfully")

if __name__ == '__main__':
    main()
