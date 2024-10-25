import boto3
import time
import sys
from botocore.exceptions import ClientError
from decimal import Decimal

def wait_for_dynamodb(max_retries=5, delay=2):
    """Wait for DynamoDB to be available"""
    print("Checking DynamoDB connection...")
    dynamodb = boto3.client('dynamodb',
                          endpoint_url='http://localhost:8000',
                          region_name='us-west-2',
                          aws_access_key_id='dummy',
                          aws_secret_access_key='dummy')
    
    for i in range(max_retries):
        try:
            dynamodb.list_tables()
            print("DynamoDB is available!")
            return True
        except Exception as e:
            print(f"Waiting for DynamoDB... ({i+1}/{max_retries})")
            time.sleep(delay)
    
    return False

def create_tables():
    """Create required DynamoDB tables"""
    dynamodb = boto3.resource('dynamodb',
                            endpoint_url='http://localhost:8000',
                            region_name='us-west-2',
                            aws_access_key_id='dummy',
                            aws_secret_access_key='dummy')
    
    try:
        # Create patients table
        patients_table = dynamodb.create_table(
            TableName='patients',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print("Created patients table")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Patients table already exists")
        else:
            raise
    
    try:
        # Create patient_progress table
        progress_table = dynamodb.create_table(
            TableName='patient_progress',
            KeySchema=[
                {'AttributeName': 'patient_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'patient_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print("Created patient_progress table")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Patient_progress table already exists")
        else:
            raise
    
    # Wait for tables to be active
    print("Waiting for tables to be active...")
    waiter = boto3.client('dynamodb',
                         endpoint_url='http://localhost:8000',
                         region_name='us-west-2',
                         aws_access_key_id='dummy',
                         aws_secret_access_key='dummy').get_waiter('table_exists')
    
    waiter.wait(TableName='patients')
    waiter.wait(TableName='patient_progress')
    print("Tables are ready!")

def verify_tables():
    """Verify tables exist and are accessible"""
    dynamodb = boto3.resource('dynamodb',
                            endpoint_url='http://localhost:8000',
                            region_name='us-west-2',
                            aws_access_key_id='dummy',
                            aws_secret_access_key='dummy')
    
    # Test patients table
    try:
        table = dynamodb.Table('patients')
        table.put_item(
            Item={
                'id': 'test',
                'name': 'Test Patient',
                'age': 30,
                'genomic_data': {
                    'gene_variants': {
                        'BRCA1': 'variant1',
                        'BRCA2': 'variant2'
                    },
                    'mutation_scores': {
                        'BRCA1': Decimal('0.8'),
                        'BRCA2': Decimal('0.6')
                    }
                },
                'medical_history': {
                    'conditions': ['test_condition'],
                    'treatments': ['test_treatment'],
                    'allergies': [],
                    'medications': []
                }
            }
        )
        print("Verified patients table")
    except Exception as e:
        print(f"Error verifying patients table: {str(e)}")
        return False
    
    # Test patient_progress table
    try:
        table = dynamodb.Table('patient_progress')
        table.put_item(
            Item={
                'patient_id': 'test',
                'timestamp': '2023-01-01T00:00:00',
                'treatment': 'Test',
                'efficacy_score': Decimal('0.5'),
                'metrics': {
                    'biomarker1': Decimal('0.9'),
                    'biomarker2': Decimal('0.7')
                }
            }
        )
        print("Verified patient_progress table")
    except Exception as e:
        print(f"Error verifying patient_progress table: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("Verifying DynamoDB setup...")
    
    if not wait_for_dynamodb():
        print("Error: DynamoDB is not available")
        sys.exit(1)
    
    try:
        create_tables()
        if verify_tables():
            print("DynamoDB setup verified successfully!")
            sys.exit(0)
        else:
            print("Error: Failed to verify tables")
            sys.exit(1)
    except Exception as e:
        print(f"Error during verification: {str(e)}")
        sys.exit(1)
