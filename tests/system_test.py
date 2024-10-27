import requests
import json
import time
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API endpoints
PATIENT_API = "http://localhost:8080"
TREATMENT_API = "http://localhost:8083"
DATA_INGESTION_API = "http://localhost:8084"

def wait_for_service(url: str, max_retries: int = 30) -> bool:
    """Wait for a service to become available"""
    logger.info(f"Waiting for service at {url}")
    for i in range(max_retries):
        try:
            response = requests.get(f"{url}/health", timeout=2)
            if response.status_code == 200:
                logger.info(f"Service at {url} is healthy")
                return True
        except requests.exceptions.RequestException:
            pass
        logger.info(f"Service not ready, retrying... ({i + 1}/{max_retries})")
        time.sleep(2)
    return False

def make_request(method: str, url: str, json_data: Optional[Dict] = None, max_retries: int = 3) -> requests.Response:
    """Make HTTP request with retries"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Making {method} request to {url}")
            if json_data:
                logger.info(f"Request data: {json.dumps(json_data, indent=2)}")
            
            if method.upper() == 'GET':
                response = requests.get(url, timeout=5)
            elif method.upper() == 'POST':
                response = requests.post(url, json=json_data, timeout=5)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response content: {json.dumps(response.json(), indent=2)}")
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"Request failed, retrying... ({attempt + 1}/{max_retries})")
            time.sleep(2)

def verify_services():
    """Verify all services are running"""
    logger.info("Verifying services...")
    services = [
        ("Patient Management", PATIENT_API),
        ("Treatment Prediction", TREATMENT_API),
        ("Data Ingestion", DATA_INGESTION_API)
    ]
    
    for name, url in services:
        if not wait_for_service(url):
            logger.error(f"{name} service is not available")
            return False
        logger.info(f"{name} service verified")
    
    return True

def test_data_ingestion():
    """Test data ingestion functionality"""
    logger.info("Testing Data Ingestion")
    try:
        # Create test patient
        patient_data = {
            "id": "TEST001",
            "name": "Test Patient",
            "age": 45,
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
                "conditions": ["condition1", "condition2"],
                "treatments": ["treatment1"],
                "allergies": ["allergy1"],
                "medications": ["med1", "med2"]
            }
        }
        
        response = make_request('POST', f"{PATIENT_API}/patient", patient_data)
        return True
    except Exception as e:
        logger.error(f"Data ingestion test failed: {str(e)}")
        return False

def test_treatment_prediction():
    """Test treatment prediction functionality"""
    logger.info("Testing Treatment Prediction")
    try:
        response = make_request('GET', f"{PATIENT_API}/patient/TEST001/treatment_recommendation")
        return True
    except Exception as e:
        logger.error(f"Treatment prediction test failed: {str(e)}")
        return False

def test_patient_management():
    """Test patient management functionality"""
    logger.info("Testing Patient Management")
    try:
        # Get patient details
        response = make_request('GET', f"{PATIENT_API}/patient/TEST001")
        
        # List all patients
        response = make_request('GET', f"{PATIENT_API}/patient")
        return True
    except Exception as e:
        logger.error(f"Patient management test failed: {str(e)}")
        return False

def run_system_test():
    """Run all system tests"""
    logger.info("Starting system tests")
    
    # First verify all services are running
    if not verify_services():
        logger.error("Service verification failed")
        sys.exit(1)
    
    tests = [
        ("Data Ingestion", test_data_ingestion),
        ("Treatment Prediction", test_treatment_prediction),
        ("Patient Management", test_patient_management)
    ]
    
    results = []
    
    try:
        for test_name, test_func in tests:
            logger.info(f"\nRunning {test_name} test...")
            try:
                success = test_func()
                results.append((test_name, success))
                if success:
                    logger.info(f"✅ {test_name} test passed!")
                else:
                    logger.error(f"❌ {test_name} test failed!")
            except Exception as e:
                logger.error(f"❌ {test_name} test failed with error: {str(e)}")
                results.append((test_name, False))
            time.sleep(1)
        
        # Print summary
        logger.info("\n=== Test Summary ===")
        all_passed = True
        for test_name, success in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
            all_passed = all_passed and success
        
        if all_passed:
            logger.info("\n✅ All System Tests Passed!")
            sys.exit(0)
        else:
            logger.error("\n❌ Some Tests Failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nUnexpected error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_system_test()
