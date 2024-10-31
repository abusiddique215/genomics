import pytest
from fastapi.testclient import TestClient
from .utils import (
    generate_test_patient,
    generate_test_patients,
    assert_valid_patient,
    assert_valid_treatment_recommendation
)

@pytest.mark.integration
class TestPatientManagementAPI:
    """Integration tests for Patient Management API"""
    
    def test_create_patient(self, patient_management_client: TestClient, test_patient, mock_logger):
        """Test creating a new patient"""
        response = patient_management_client.post("/patients", json=test_patient)
        assert response.status_code == 200
        assert response.json()["message"] == "Patient created successfully"
        
        # Verify patient was created
        get_response = patient_management_client.get(f"/patients/{test_patient['id']}")
        assert get_response.status_code == 200
        created_patient = get_response.json()
        assert_valid_patient(created_patient)
        assert created_patient["id"] == test_patient["id"]
    
    def test_get_patient(self, patient_management_client: TestClient, test_patient):
        """Test retrieving a patient"""
        # Create test patient
        patient_management_client.post("/patients", json=test_patient)
        
        # Get patient
        response = patient_management_client.get(f"/patients/{test_patient['id']}")
        assert response.status_code == 200
        patient = response.json()
        assert_valid_patient(patient)
        assert patient["id"] == test_patient["id"]
    
    def test_list_patients(self, patient_management_client: TestClient):
        """Test listing all patients"""
        # Create test patients
        test_patients = generate_test_patients(3)
        for patient in test_patients:
            patient_management_client.post("/patients", json=patient)
        
        # List patients
        response = patient_management_client.get("/patients")
        assert response.status_code == 200
        patients = response.json()
        assert isinstance(patients, list)
        assert len(patients) >= 3
        for patient in patients:
            assert_valid_patient(patient)
    
    def test_get_treatment_recommendation(
        self,
        patient_management_client: TestClient,
        test_patient,
        mock_requests
    ):
        """Test getting treatment recommendation"""
        # Create test patient
        patient_management_client.post("/patients", json=test_patient)
        
        # Get recommendation
        response = patient_management_client.get(
            f"/patients/{test_patient['id']}/treatment_recommendation"
        )
        assert response.status_code == 200
        recommendation = response.json()
        assert_valid_treatment_recommendation(recommendation)
    
    def test_patient_not_found(self, patient_management_client: TestClient):
        """Test handling of non-existent patient"""
        response = patient_management_client.get("/patients/NONEXISTENT")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.parametrize("invalid_field", [
        {"age": "invalid"},
        {"genomic_data": "invalid"},
        {"medical_history": None}
    ])
    def test_invalid_patient_data(
        self,
        patient_management_client: TestClient,
        test_patient,
        invalid_field
    ):
        """Test handling of invalid patient data"""
        invalid_patient = {**test_patient, **invalid_field}
        response = patient_management_client.post("/patients", json=invalid_patient)
        assert response.status_code == 422

@pytest.mark.unit
class TestPatientManagementUnit:
    """Unit tests for Patient Management service"""
    
    def test_patient_validation(self, test_patient):
        """Test patient data validation"""
        from services.patient_management.app import validate_patient
        
        # Valid patient
        assert validate_patient(test_patient) is None
        
        # Invalid patient
        with pytest.raises(ValueError):
            validate_patient({})
    
    def test_patient_transformation(self, test_patient):
        """Test patient data transformation"""
        from services.patient_management.app import transform_patient_data
        
        transformed = transform_patient_data(test_patient)
        assert isinstance(transformed["age"], str)
        assert all(
            isinstance(score, str)
            for score in transformed["genomic_data"]["mutation_scores"].values()
        )
    
    @pytest.mark.asyncio
    async def test_db_operations(self, mock_dynamodb_client, test_patient):
        """Test database operations"""
        from services.patient_management.app import (
            create_patient,
            get_patient,
            list_patients
        )
        
        # Create patient
        await create_patient(test_patient)
        
        # Get patient
        patient = await get_patient(test_patient["id"])
        assert patient["id"] == test_patient["id"]
        
        # List patients
        patients = await list_patients()
        assert len(patients) > 0
        assert any(p["id"] == test_patient["id"] for p in patients)

@pytest.mark.slow
class TestPatientManagementPerformance:
    """Performance tests for Patient Management service"""
    
    def test_bulk_operations(self, patient_management_client: TestClient):
        """Test bulk patient operations"""
        # Create many patients
        test_patients = generate_test_patients(100)
        start_time = time.time()
        
        for patient in test_patients:
            response = patient_management_client.post("/patients", json=patient)
            assert response.status_code == 200
        
        duration = time.time() - start_time
        assert duration < 10  # Should complete within 10 seconds
    
    def test_concurrent_requests(self, patient_management_client: TestClient):
        """Test concurrent API requests"""
        import asyncio
        import aiohttp
        
        async def make_requests():
            async with aiohttp.ClientSession() as session:
                tasks = []
                for _ in range(10):
                    task = session.get(f"{PATIENT_API}/patients")
                    tasks.append(task)
                responses = await asyncio.gather(*tasks)
                return [r.status for r in responses]
        
        status_codes = asyncio.run(make_requests())
        assert all(code == 200 for code in status_codes)
