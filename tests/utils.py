from typing import Dict, Any, Optional, List
import json
import pytest
from datetime import datetime, timedelta
import uuid
import random

def generate_test_patient(
    patient_id: Optional[str] = None,
    age: Optional[int] = None,
    conditions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Generate a test patient record with optional customization"""
    return {
        "id": patient_id or f"TEST{uuid.uuid4().hex[:6].upper()}",
        "name": f"Test Patient {random.randint(1, 1000)}",
        "age": age or random.randint(20, 80),
        "genomic_data": {
            "gene_variants": {
                "BRCA1": f"variant{random.randint(1, 5)}",
                "BRCA2": f"variant{random.randint(1, 5)}"
            },
            "mutation_scores": {
                "BRCA1": str(round(random.uniform(0.1, 1.0), 2)),
                "BRCA2": str(round(random.uniform(0.1, 1.0), 2))
            }
        },
        "medical_history": {
            "conditions": conditions or [
                f"condition{random.randint(1, 5)}"
                for _ in range(random.randint(1, 3))
            ],
            "treatments": [
                f"treatment{random.randint(1, 5)}"
                for _ in range(random.randint(1, 3))
            ],
            "allergies": [
                f"allergy{random.randint(1, 5)}"
                for _ in range(random.randint(0, 2))
            ],
            "medications": [
                f"med{random.randint(1, 5)}"
                for _ in range(random.randint(1, 3))
            ]
        }
    }

def generate_test_patients(count: int) -> List[Dict[str, Any]]:
    """Generate multiple test patient records"""
    return [generate_test_patient() for _ in range(count)]

def assert_valid_patient(patient: Dict[str, Any]):
    """Assert that a patient record is valid"""
    assert isinstance(patient, dict)
    assert "id" in patient
    assert "name" in patient
    assert "age" in patient
    assert "genomic_data" in patient
    assert "medical_history" in patient
    
    assert isinstance(patient["genomic_data"], dict)
    assert "gene_variants" in patient["genomic_data"]
    assert "mutation_scores" in patient["genomic_data"]
    
    assert isinstance(patient["medical_history"], dict)
    assert "conditions" in patient["medical_history"]
    assert "treatments" in patient["medical_history"]
    assert "allergies" in patient["medical_history"]
    assert "medications" in patient["medical_history"]

def assert_valid_treatment_recommendation(recommendation: Dict[str, Any]):
    """Assert that a treatment recommendation is valid"""
    assert isinstance(recommendation, dict)
    assert "recommended_treatment" in recommendation
    assert "efficacy" in recommendation
    assert "confidence_level" in recommendation
    
    assert isinstance(recommendation["efficacy"], (int, float))
    assert 0 <= recommendation["efficacy"] <= 1
    assert recommendation["confidence_level"] in ["low", "medium", "high"]

class AsyncMock:
    """Mock for async functions"""
    def __init__(self, return_value=None):
        self.return_value = return_value
        self.calls = []
    
    async def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.return_value

def mock_aws_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a mock AWS response"""
    return {
        'ResponseMetadata': {
            'RequestId': str(uuid.uuid4()),
            'HTTPStatusCode': 200,
        },
        **data
    }

class MockContext:
    """Mock AWS Lambda context"""
    def __init__(self):
        self.function_name = "test-function"
        self.function_version = "$LATEST"
        self.invoked_function_arn = f"arn:aws:lambda:us-west-2:123456789012:function:{self.function_name}"
        self.memory_limit_in_mb = 128
        self.aws_request_id = str(uuid.uuid4())
        self.log_group_name = f"/aws/lambda/{self.function_name}"
        self.log_stream_name = "2024/01/01/[$LATEST]123456789"
        self.identity = None
        self.client_context = None
        
        self._remaining_time_ms = 300000
    
    def get_remaining_time_in_millis(self):
        return self._remaining_time_ms

def compare_patients(patient1: Dict[str, Any], patient2: Dict[str, Any]):
    """Compare two patient records, ignoring non-essential differences"""
    essential_fields = ['id', 'name', 'age', 'genomic_data', 'medical_history']
    return all(
        patient1.get(field) == patient2.get(field)
        for field in essential_fields
    )

def setup_test_database(dynamodb_client, patients: List[Dict[str, Any]]):
    """Set up test database with initial data"""
    for patient in patients:
        dynamodb_client.put_item(
            TableName='patients',
            Item={
                'id': {'S': patient['id']},
                'data': {'S': json.dumps(patient)}
            }
        )

@pytest.fixture
def cleanup_test_database(dynamodb_client):
    """Cleanup test database after test"""
    yield
    dynamodb_client.delete_table(TableName='patients')
    dynamodb_client.delete_table(TableName='patient_progress')
