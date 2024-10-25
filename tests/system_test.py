import requests
import json
import time
import sys
from datetime import datetime, timedelta
from typing import Dict, Any
from decimal import Decimal
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# API endpoints
PATIENT_API = "http://localhost:8501"
TREATMENT_API = "http://localhost:8083"
DATA_INGESTION_API = "http://localhost:8084"

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

def make_request(method: str, url: str, json_data: Dict[str, Any] = None, max_retries: int = 3) -> requests.Response:
    """Make HTTP request with retries"""
    for attempt in range(max_retries):
        try:
            logger.debug(f"Making {method} request to {url}")
            if json_data:
                logger.debug(f"Request data: {json.dumps(json_data, cls=DecimalEncoder, indent=2)}")
            
            if method.upper() == 'GET':
                response = requests.get(url, timeout=5)
            elif method.upper() == 'POST':
                # Convert Decimal objects to strings for JSON serialization
                if json_data:
                    json_data = json.loads(json.dumps(json_data, cls=DecimalEncoder))
                response = requests.post(url, json=json_data, timeout=5)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response content: {response.text}")
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                logger.error(f"Request failed after {max_retries} attempts: {str(e)}")
                raise
            logger.warning(f"Request failed, retrying... ({attempt + 1}/{max_retries})")
            time.sleep(2)

def verify_dynamodb_connection():
    """Verify DynamoDB connection"""
    print("\n=== Verifying DynamoDB Connection ===")
    try:
        # First check service health
        logger.info("Checking service health...")
        health_response = make_request('GET', f"{PATIENT_API}/health")
        if health_response.status_code != 200:
            logger.error("Health check failed")
            return False
        
        # Create a test patient
        test_data = {
            "id": "TEST000",
            "name": "Connection Test",
            "age": 30,
            "genomic_data": {
                "gene_variants": {
                    "BRCA1": "variant1",
                    "BRCA2": "variant2"
                },
                "mutation_scores": {
                    "BRCA1": "0.8",
                    "BRCA2": "0.6"
                }
            },
            "medical_history": {
                "conditions": ["test_condition"],
                "treatments": ["test_treatment"],
                "allergies": [],
                "medications": []
            }
        }
        
        logger.info("Creating test patient...")
        response = make_request('POST', f"{PATIENT_API}/patient", test_data)
        print("DynamoDB connection verified!")
        return True
    except Exception as e:
        logger.error(f"DynamoDB connection failed: {str(e)}")
        return False

def run_system_test():
    """Run system tests"""
    # First verify DynamoDB connection
    if not verify_dynamodb_connection():
        print("\n❌ DynamoDB connection failed! Please check your setup.")
        sys.exit(1)
    
    print("\n✅ Initial verification passed!")
    sys.exit(0)

if __name__ == "__main__":
    run_system_test()
