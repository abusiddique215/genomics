import pytest
import asyncio
from typing import Dict, Any, Generator
import boto3
from moto import mock_dynamodb
import os
from fastapi.testclient import TestClient
import json
from datetime import datetime

# Set test environment
os.environ['ENV'] = 'test'
os.environ['AWS_DEFAULT_REGION'] = 'us-west-2'

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def mock_dynamodb_client():
    """Create a mocked DynamoDB client"""
    with mock_dynamodb():
        client = boto3.client('dynamodb', region_name='us-west-2')
        
        # Create test tables
        client.create_table(
            TableName='patients',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        client.create_table(
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
        
        yield client

@pytest.fixture
def test_patient() -> Dict[str, Any]:
    """Create a test patient record"""
    return {
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

@pytest.fixture
def mock_ai_model():
    """Mock AI model predictions"""
    class MockModel:
        def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "recommended_treatment": "Treatment A",
                "efficacy": 0.85,
                "confidence_level": "high"
            }
    return MockModel()

@pytest.fixture
def patient_management_client(mock_dynamodb_client):
    """Create a test client for the patient management service"""
    from services.patient_management.app import app
    return TestClient(app)

@pytest.fixture
def treatment_prediction_client(mock_ai_model):
    """Create a test client for the treatment prediction service"""
    from services.treatment_prediction.main import app
    return TestClient(app)

@pytest.fixture
def data_ingestion_client():
    """Create a test client for the data ingestion service"""
    from services.data_ingestion.main import app
    return TestClient(app)

class MockResponse:
    """Mock HTTP response"""
    def __init__(self, status_code: int, json_data: Dict[str, Any]):
        self.status_code = status_code
        self._json_data = json_data
    
    def json(self):
        return self._json_data

@pytest.fixture
def mock_requests(monkeypatch):
    """Mock requests to external services"""
    def mock_get(*args, **kwargs):
        if 'health' in args[0]:
            return MockResponse(200, {"status": "healthy"})
        return MockResponse(404, {"error": "Not found"})
    
    def mock_post(*args, **kwargs):
        if 'predict' in args[0]:
            return MockResponse(200, {
                "recommended_treatment": "Treatment A",
                "efficacy": 0.85,
                "confidence_level": "high"
            })
        return MockResponse(404, {"error": "Not found"})
    
    import requests
    monkeypatch.setattr(requests, "get", mock_get)
    monkeypatch.setattr(requests, "post", mock_post)

@pytest.fixture
def mock_logger(monkeypatch):
    """Mock logger to capture log messages"""
    class MockLogger:
        def __init__(self):
            self.messages = []
        
        def _log(self, level: str, message: str, **kwargs):
            self.messages.append({
                'level': level,
                'message': message,
                'kwargs': kwargs
            })
        
        def debug(self, message: str, **kwargs):
            self._log('debug', message, **kwargs)
        
        def info(self, message: str, **kwargs):
            self._log('info', message, **kwargs)
        
        def warning(self, message: str, **kwargs):
            self._log('warning', message, **kwargs)
        
        def error(self, message: str, **kwargs):
            self._log('error', message, **kwargs)
    
    logger = MockLogger()
    from services.utils.logging import get_logger
    monkeypatch.setattr(get_logger, "return_value", logger)
    return logger

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection based on markers"""
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="run slow tests"
    )
