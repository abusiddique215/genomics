import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv
import sys

load_dotenv()

print(f"AWS_ACCESS_KEY_ID: {os.getenv('AWS_ACCESS_KEY_ID')}")
print(f"AWS_SECRET_ACCESS_KEY: {'*' * len(os.getenv('AWS_SECRET_ACCESS_KEY', ''))}")
print(f"AWS_DEFAULT_REGION: {os.getenv('AWS_DEFAULT_REGION')}")

def test_dynamodb_connection():
    try:
        print("Creating DynamoDB resource...")
        dynamodb = boto3.resource('dynamodb')
        print("DynamoDB resource created successfully")
        
        print("Accessing 'Patients' table...")
        table = dynamodb.Table('Patients')
        print("'Patients' table accessed successfully")
        
        print("Performing a scan operation...")
        response = table.scan(Limit=1)
        print(f"Scan operation successful. Items retrieved: {len(response.get('Items', []))}")
        
        print("DynamoDB connection test passed")
        return True
    except ClientError as e:
        print(f"ClientError: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    result = test_dynamodb_connection()
    print(f"DynamoDB connection test {'passed' if result else 'failed'}")
