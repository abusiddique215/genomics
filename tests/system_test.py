import requests
import json
import time
import sys
from datetime import datetime, timedelta
from typing import Dict, Any

# API endpoints
PATIENT_API = "http://localhost:8501"
TREATMENT_API = "http://localhost:8083"
DATA_INGESTION_API = "http://localhost:8084"

def make_request(method: str, url: str, json_data: Dict[str, Any] = None, max_retries: int = 3) -> requests.Response:
    """Make HTTP request with retries"""
    for attempt in range(max_retries):
        try:
            if method.upper() == 'GET':
                response = requests.get(url, timeout=5)
            elif method.upper() == 'POST':
                response = requests.post(url, json=json_data, timeout=5)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            print(f"Request failed, retrying... ({attempt + 1}/{max_retries})")
            time.sleep(2)

def verify_dynamodb_connection():
    """Verify DynamoDB connection"""
    print("\n=== Verifying DynamoDB Connection ===")
    try:
        # Create a test patient with valid data structure
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
                    "BRCA1": 0.8,
                    "BRCA2": 0.6
                }
            },
            "medical_history": {
                "conditions": ["test_condition"],
                "treatments": ["test_treatment"],
                "allergies": [],
                "medications": []
            }
        }
        
        response = make_request('POST', f"{PATIENT_API}/patient", test_data)
        print("DynamoDB connection verified!")
        return True
    except Exception as e:
        print(f"DynamoDB connection failed: {str(e)}")
        return False

def test_data_ingestion():
    print("\n=== Testing Data Ingestion ===")
    
    # Test genomic data ingestion
    genomic_data = {
        "gene_variants": {
            "BRCA1": "variant1",
            "BRCA2": "variant2"
        },
        "mutation_scores": {
            "BRCA1": 0.8,
            "BRCA2": 0.6
        }
    }
    
    medical_history = {
        "conditions": ["condition1", "condition2"],
        "treatments": ["treatment1"],
        "allergies": ["allergy1"],
        "medications": ["med1", "med2"]
    }
    
    # Create test patient
    patient_data = {
        "id": "TEST001",
        "name": "Test Patient",
        "age": 45,
        "genomic_data": genomic_data,
        "medical_history": medical_history
    }
    
    try:
        response = make_request('POST', f"{PATIENT_API}/patient", patient_data)
        print(f"Create patient response: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_treatment_prediction():
    print("\n=== Testing Treatment Prediction ===")
    
    try:
        # Get treatment recommendation
        response = make_request('GET', f"{PATIENT_API}/patient/TEST001/treatment_recommendation")
        print(f"Treatment recommendation response: {response.status_code}")
        print(f"Recommendation: {json.dumps(response.json(), indent=2)}")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_progress_tracking():
    print("\n=== Testing Progress Tracking ===")
    
    try:
        # Add progress entry
        progress_data = {
            "treatment": "Treatment A",
            "efficacy_score": 0.85,
            "side_effects": ["mild fatigue"],
            "notes": "Patient responding well to treatment",
            "metrics": {"biomarker1": 0.9, "biomarker2": 0.7},
            "next_appointment": (datetime.now() + timedelta(days=30)).isoformat()
        }
        
        response = make_request('POST', f"{PATIENT_API}/patient/TEST001/progress", progress_data)
        print(f"Add progress response: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Get progress history
        response = make_request('GET', f"{PATIENT_API}/patient/TEST001/progress")
        print(f"Get progress response: {response.status_code}")
        print(f"Progress history: {json.dumps(response.json(), indent=2)}")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_patient_management():
    print("\n=== Testing Patient Management ===")
    
    try:
        # Get patient details
        response = make_request('GET', f"{PATIENT_API}/patient/TEST001")
        print(f"Get patient response: {response.status_code}")
        print(f"Patient details: {json.dumps(response.json(), indent=2)}")
        
        # List all patients
        response = make_request('GET', f"{PATIENT_API}/patient")
        print(f"List patients response: {response.status_code}")
        print(f"Total patients: {len(response.json())}")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def run_system_test():
    """Run all system tests"""
    # First verify DynamoDB connection
    if not verify_dynamodb_connection():
        print("\n❌ DynamoDB connection failed! Please check your setup.")
        sys.exit(1)

    tests = [
        ("Data Ingestion", test_data_ingestion),
        ("Treatment Prediction", test_treatment_prediction),
        ("Progress Tracking", test_progress_tracking),
        ("Patient Management", test_patient_management)
    ]
    
    results = []
    
    try:
        for test_name, test_func in tests:
            print(f"\nRunning {test_name} test...")
            try:
                success = test_func()
                results.append((test_name, success))
                if success:
                    print(f"✅ {test_name} test passed!")
                else:
                    print(f"❌ {test_name} test failed!")
            except Exception as e:
                print(f"❌ {test_name} test failed with error: {str(e)}")
                results.append((test_name, False))
            time.sleep(1)
        
        # Print summary
        print("\n=== Test Summary ===")
        all_passed = True
        for test_name, success in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{test_name}: {status}")
            all_passed = all_passed and success
        
        if all_passed:
            print("\n✅ All System Tests Passed!")
            sys.exit(0)
        else:
            print("\n❌ Some Tests Failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_system_test()
