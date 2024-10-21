print("Executing patient_management main module")

import boto3
from dotenv import load_dotenv
import os
import sys
import time
import threading
import logging
from services.patient_management.app import app

print("All modules imported successfully")

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("Starting patient_management service...")

# Global variable to store the DynamoDB table
table = None

def initialize_dynamodb(timeout=60):
    global table
    start_time = time.time()
    
    def _initialize():
        global table
        try:
            logger.info("Initializing AWS DynamoDB client...")
            logger.info("Creating DynamoDB resource...")
            dynamodb = boto3.resource('dynamodb')
            logger.info("DynamoDB resource created successfully")
            
            logger.info("Accessing 'Patients' table...")
            table = dynamodb.Table('Patients')
            logger.info("'Patients' table accessed successfully")
            
            # Test the connection by performing a scan operation
            logger.info("Testing DynamoDB connection with a scan operation...")
            response = table.scan(Limit=1)
            logger.info(f"Scan operation successful. Items retrieved: {len(response.get('Items', []))}")
            
            logger.info("DynamoDB client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB: {str(e)}", exc_info=True)
            raise

    thread = threading.Thread(target=_initialize)
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        logger.error(f"DynamoDB initialization timed out after {timeout} seconds")
        raise Exception("DynamoDB initialization timed out")
    
    if table is None:
        logger.error("Failed to initialize DynamoDB")
        raise Exception("Failed to initialize DynamoDB")

    logger.info(f"DynamoDB initialization completed in {time.time() - start_time:.2f} seconds")

# Initialize DynamoDB with a timeout
try:
    print("Initializing DynamoDB...")
    initialize_dynamodb()
    print("DynamoDB initialized successfully")
except Exception as e:
    print(f"Error during DynamoDB initialization: {str(e)}")
    sys.exit(1)

print("Routes defined:")
for route in app.routes:
    print(f"  {route.methods} {route.path}")

print("patient_management service setup completed")
