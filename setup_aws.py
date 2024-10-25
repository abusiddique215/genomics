import boto3
import os
from botocore.exceptions import ClientError
import json
import time

def verify_dynamodb_tables():
    """Verify DynamoDB tables exist and are accessible"""
    try:
        dynamodb = boto3.resource('dynamodb',
                                endpoint_url='http://localhost:8000',
                                region_name='us-west-2',
                                aws_access_key_id='dummy',
                                aws_secret_access_key='dummy')
        
        # Check patients table
        patients_table = dynamodb.Table('patients')
        patients_table.put_item(
            Item={
                'id': 'TEST000',
                'name': 'Test Patient',
                'age': 30,
                'genomic_data': {'test': 'data'},
                'medical_history': {'test': 'history'}
            }
        )
        
        # Check patient_progress table
        progress_table = dynamodb.Table('patient_progress')
        progress_table.put_item(
            Item={
                'patient_id': 'TEST000',
                'timestamp': '2023-01-01T00:00:00',
                'treatment': 'Test Treatment',
                'efficacy_score': 0.5
            }
        )
        
        print("DynamoDB tables verified successfully!")
        return True
        
    except Exception as e:
        print(f"Error verifying DynamoDB tables: {str(e)}")
        return False

def setup_dynamodb():
    """Set up DynamoDB tables"""
    try:
        dynamodb = boto3.resource('dynamodb',
                                endpoint_url='http://localhost:8000',
                                region_name='us-west-2',
                                aws_access_key_id='dummy',
                                aws_secret_access_key='dummy')
        
        # Create patients table
        try:
            patients_table = dynamodb.create_table(
                TableName='patients',
                KeySchema=[
                    {
                        'AttributeName': 'id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'id',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            print("Created patients table")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print("Patients table already exists")
            else:
                raise
        
        # Create patient_progress table
        try:
            progress_table = dynamodb.create_table(
                TableName='patient_progress',
                KeySchema=[
                    {
                        'AttributeName': 'patient_id',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'timestamp',
                        'KeyType': 'RANGE'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'patient_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'timestamp',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            print("Created patient_progress table")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print("Patient_progress table already exists")
            else:
                raise
        
        # Wait for tables to be created
        print("Waiting for tables to be created...")
        time.sleep(5)
        
        # Verify tables
        if not verify_dynamodb_tables():
            return False
        
        return True
        
    except Exception as e:
        print(f"Error setting up DynamoDB: {str(e)}")
        return False

def create_env_file():
    """Create .env file with necessary configuration"""
    env_content = """
# AWS Configuration
AWS_ACCESS_KEY_ID=dummy
AWS_SECRET_ACCESS_KEY=dummy
AWS_DEFAULT_REGION=us-west-2
DYNAMODB_ENDPOINT_URL=http://localhost:8000

# Service Configuration
PATIENT_SERVICE_PORT=8501
TREATMENT_SERVICE_PORT=8083
DATA_INGESTION_PORT=8084
    """
    
    with open('.env', 'w') as f:
        f.write(env_content.strip())
    
    print(".env file created successfully!")
    return True

def main():
    """Run setup process"""
    print("Setting up development environment...")
    
    # Create .env file
    if not create_env_file():
        print("Failed to create .env file")
        return False
    
    # Set up DynamoDB tables
    if not setup_dynamodb():
        print("Failed to set up DynamoDB tables")
        return False
    
    print("\nSetup completed successfully!")
    print("\nYou can now run the services using:")
    print("python start_services.py")
    return True

if __name__ == "__main__":
    main()
