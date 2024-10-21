import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

load_dotenv()

def test_aws_connection():
    try:
        # Initialize AWS DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('Patients')

        # Test DynamoDB connection
        response = table.scan(Limit=1)
        print("DynamoDB connection successful")
        print(f"Items in 'Patients' table: {response.get('Items', [])}")

        # Test S3 connection
        s3 = boto3.client('s3')
        buckets = s3.list_buckets()
        print("S3 connection successful")
        print(f"S3 Buckets: {[bucket['Name'] for bucket in buckets['Buckets']]}")

        return True
    except ClientError as e:
        print(f"AWS connection error: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"AWS_ACCESS_KEY_ID: {os.getenv('AWS_ACCESS_KEY_ID')}")
    print(f"AWS_SECRET_ACCESS_KEY: {'*' * len(os.getenv('AWS_SECRET_ACCESS_KEY', ''))}")
    print(f"AWS_DEFAULT_REGION: {os.getenv('AWS_DEFAULT_REGION')}")
    
    result = test_aws_connection()
    print(f"AWS connection test {'passed' if result else 'failed'}")
