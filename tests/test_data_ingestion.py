import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any, List
import json
from .utils import (
    generate_test_patient,
    generate_test_patients,
    assert_valid_patient
)

@pytest.mark.integration
class TestDataIngestionAPI:
    """Integration tests for Data Ingestion API"""
    
    def test_ingest_patient(
        self,
        data_ingestion_client: TestClient,
        test_patient: Dict[str, Any],
        mock_logger
    ):
        """Test patient data ingestion"""
        response = data_ingestion_client.post(
            "/ingest/patient",
            json=test_patient
        )
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "success"
        assert "patient_id" in result
    
    def test_batch_ingestion(
        self,
        data_ingestion_client: TestClient
    ):
        """Test batch patient data ingestion"""
        test_patients = generate_test_patients(5)
        response = data_ingestion_client.post(
            "/ingest/patients/batch",
            json={"patients": test_patients}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["success_count"] == 5
        assert result["failed_count"] == 0
    
    def test_file_upload(
        self,
        data_ingestion_client: TestClient,
        tmp_path
    ):
        """Test patient data file upload"""
        # Create test file
        test_patients = generate_test_patients(3)
        file_path = tmp_path / "patients.json"
        with open(file_path, "w") as f:
            json.dump(test_patients, f)
        
        # Upload file
        with open(file_path, "rb") as f:
            response = data_ingestion_client.post(
                "/ingest/file",
                files={"file": ("patients.json", f, "application/json")}
            )
        
        assert response.status_code == 200
        result = response.json()
        assert result["processed_count"] == 3
    
    def test_invalid_data_handling(
        self,
        data_ingestion_client: TestClient
    ):
        """Test handling of invalid data"""
        # Invalid patient data
        response = data_ingestion_client.post(
            "/ingest/patient",
            json={"invalid": "data"}
        )
        assert response.status_code == 422
        
        # Invalid batch data
        response = data_ingestion_client.post(
            "/ingest/patients/batch",
            json={"patients": [{"invalid": "data"}]}
        )
        assert response.status_code == 422
        
        # Invalid file format
        response = data_ingestion_client.post(
            "/ingest/file",
            files={"file": ("test.txt", b"invalid data", "text/plain")}
        )
        assert response.status_code == 400

@pytest.mark.unit
class TestDataIngestionUnit:
    """Unit tests for Data Ingestion service"""
    
    def test_data_validation(self, test_patient):
        """Test data validation"""
        from services.data_ingestion.main import validate_patient_data
        
        # Valid data
        assert validate_patient_data(test_patient) is True
        
        # Invalid data
        assert validate_patient_data({}) is False
        assert validate_patient_data({"invalid": "data"}) is False
    
    def test_data_transformation(self, test_patient):
        """Test data transformation"""
        from services.data_ingestion.main import transform_patient_data
        
        transformed = transform_patient_data(test_patient)
        assert "metadata" in transformed
        assert "ingestion_timestamp" in transformed["metadata"]
    
    def test_file_processing(self, tmp_path):
        """Test file processing"""
        from services.data_ingestion.main import process_patient_file
        
        # Create test file
        test_patients = generate_test_patients(3)
        file_path = tmp_path / "patients.json"
        with open(file_path, "w") as f:
            json.dump(test_patients, f)
        
        # Process file
        result = process_patient_file(file_path)
        assert result["processed_count"] == 3
        assert result["success_count"] == 3

@pytest.mark.slow
class TestDataIngestionPerformance:
    """Performance tests for Data Ingestion service"""
    
    def test_large_batch_ingestion(
        self,
        data_ingestion_client: TestClient
    ):
        """Test ingestion of large batch of patients"""
        test_patients = generate_test_patients(100)
        
        start_time = time.time()
        response = data_ingestion_client.post(
            "/ingest/patients/batch",
            json={"patients": test_patients}
        )
        duration = time.time() - start_time
        
        assert response.status_code == 200
        assert duration < 10.0  # Should complete within 10 seconds
    
    def test_concurrent_ingestion(
        self,
        data_ingestion_client: TestClient
    ):
        """Test concurrent data ingestion"""
        test_patients = generate_test_patients(20)
        
        async def run_concurrent_ingestion():
            tasks = []
            for patient in test_patients:
                task = asyncio.create_task(
                    data_ingestion_client.post(
                        "/ingest/patient",
                        json=patient
                    )
                )
                tasks.append(task)
            
            start_time = time.time()
            responses = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            return responses, total_time
        
        responses, total_time = asyncio.run(run_concurrent_ingestion())
        
        assert all(r.status_code == 200 for r in responses)
        assert total_time < 5.0  # Should complete within 5 seconds
