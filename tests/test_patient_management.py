from fastapi.testclient import TestClient
from services.patient_management.main import app
import pytest

client = TestClient(app)

@pytest.fixture
def sample_patient_data():
    return {
        "id": "test123",
        "name": "Test Patient",
        "age": 30,
        "genomic_data": {"gene1": "variant1"},
        "medical_history": {"condition1": "details1"}
    }

def test_create_patient(sample_patient_data):
    response = client.post("/patient", json=sample_patient_data)
    assert response.status_code == 200
    assert response.json() == {"message": "Patient created successfully"}

def test_get_patient(sample_patient_data):
    # First, create a patient
    client.post("/patient", json=sample_patient_data)
    
    # Then, retrieve the patient
    response = client.get(f"/patient/{sample_patient_data['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == sample_patient_data["id"]

def test_update_patient(sample_patient_data):
    # First, create a patient
    client.post("/patient", json=sample_patient_data)
    
    # Then, update the patient
    updated_data = sample_patient_data.copy()
    updated_data["age"] = 31
    response = client.put(f"/patient/{sample_patient_data['id']}", json=updated_data)
    assert response.status_code == 200
    assert response.json() == {"message": "Patient updated successfully"}

def test_get_nonexistent_patient():
    response = client.get("/patient/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Patient not found"