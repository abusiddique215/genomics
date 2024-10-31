import pytest
import asyncio
import time
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from .utils import (
    generate_test_patient,
    generate_test_patients,
    assert_valid_patient,
    assert_valid_treatment_recommendation
)

@pytest.mark.integration
class TestSystemIntegration:
    """System-wide integration tests"""
    
    def test_end_to_end_flow(
        self,
        patient_management_client: TestClient,
        treatment_prediction_client: TestClient,
        data_ingestion_client: TestClient,
        test_patient: Dict[str, Any],
        mock_logger
    ):
        """Test complete end-to-end flow"""
        # 1. Ingest patient data
        ingest_response = data_ingestion_client.post(
            "/ingest/patient",
            json=test_patient
        )
        assert ingest_response.status_code == 200
        
        # 2. Verify patient was created
        get_response = patient_management_client.get(
            f"/patients/{test_patient['id']}"
        )
        assert get_response.status_code == 200
        stored_patient = get_response.json()
        assert_valid_patient(stored_patient)
        
        # 3. Get treatment recommendation
        prediction_response = treatment_prediction_client.post(
            "/predict",
            json={
                "genomic_data": test_patient["genomic_data"],
                "medical_history": test_patient["medical_history"]
            }
        )
        assert prediction_response.status_code == 200
        recommendation = prediction_response.json()
        assert_valid_treatment_recommendation(recommendation)
        
        # 4. Update patient with recommendation
        update_response = patient_management_client.post(
            f"/patients/{test_patient['id']}/treatments",
            json={"treatment": recommendation["recommended_treatment"]}
        )
        assert update_response.status_code == 200
        
        # 5. Verify updated patient record
        final_response = patient_management_client.get(
            f"/patients/{test_patient['id']}"
        )
        assert final_response.status_code == 200
        final_patient = final_response.json()
        assert recommendation["recommended_treatment"] in \
            final_patient["medical_history"]["treatments"]
    
    @pytest.mark.slow
    def test_system_load(
        self,
        patient_management_client: TestClient,
        treatment_prediction_client: TestClient,
        data_ingestion_client: TestClient
    ):
        """Test system under load"""
        # Generate test data
        test_patients = generate_test_patients(10)
        
        # Concurrent ingestion
        async def ingest_patients():
            tasks = []
            for patient in test_patients:
                task = asyncio.create_task(
                    data_ingestion_client.post(
                        "/ingest/patient",
                        json=patient
                    )
                )
                tasks.append(task)
            return await asyncio.gather(*tasks)
        
        responses = asyncio.run(ingest_patients())
        assert all(r.status_code == 200 for r in responses)
        
        # Verify all patients and get recommendations
        for patient in test_patients:
            # Get patient
            get_response = patient_management_client.get(
                f"/patients/{patient['id']}"
            )
            assert get_response.status_code == 200
            
            # Get recommendation
            pred_response = treatment_prediction_client.post(
                "/predict",
                json={
                    "genomic_data": patient["genomic_data"],
                    "medical_history": patient["medical_history"]
                }
            )
            assert pred_response.status_code == 200
    
    def test_error_handling(
        self,
        patient_management_client: TestClient,
        treatment_prediction_client: TestClient,
        data_ingestion_client: TestClient
    ):
        """Test system-wide error handling"""
        # Test invalid data ingestion
        ingest_response = data_ingestion_client.post(
            "/ingest/patient",
            json={"invalid": "data"}
        )
        assert ingest_response.status_code == 422
        
        # Test non-existent patient
        get_response = patient_management_client.get("/patients/NONEXISTENT")
        assert get_response.status_code == 404
        
        # Test invalid prediction request
        pred_response = treatment_prediction_client.post(
            "/predict",
            json={"invalid": "data"}
        )
        assert pred_response.status_code == 422
    
    def test_data_consistency(
        self,
        patient_management_client: TestClient,
        data_ingestion_client: TestClient,
        test_patient: Dict[str, Any]
    ):
        """Test data consistency across services"""
        # Ingest patient
        ingest_response = data_ingestion_client.post(
            "/ingest/patient",
            json=test_patient
        )
        assert ingest_response.status_code == 200
        
        # Get patient from management service
        get_response = patient_management_client.get(
            f"/patients/{test_patient['id']}"
        )
        assert get_response.status_code == 200
        stored_patient = get_response.json()
        
        # Compare data
        assert stored_patient["id"] == test_patient["id"]
        assert stored_patient["genomic_data"] == test_patient["genomic_data"]
        assert stored_patient["medical_history"] == test_patient["medical_history"]
    
    @pytest.mark.slow
    def test_service_recovery(
        self,
        patient_management_client: TestClient,
        treatment_prediction_client: TestClient,
        data_ingestion_client: TestClient,
        test_patient: Dict[str, Any]
    ):
        """Test system recovery after service failures"""
        # Simulate service restart by recreating clients
        from services.patient_management.app import app as patient_app
        from services.treatment_prediction.main import app as prediction_app
        from services.data_ingestion.main import app as ingestion_app
        
        new_patient_client = TestClient(patient_app)
        new_prediction_client = TestClient(prediction_app)
        new_ingestion_client = TestClient(ingestion_app)
        
        # Test operations with new clients
        ingest_response = new_ingestion_client.post(
            "/ingest/patient",
            json=test_patient
        )
        assert ingest_response.status_code == 200
        
        get_response = new_patient_client.get(
            f"/patients/{test_patient['id']}"
        )
        assert get_response.status_code == 200
        
        pred_response = new_prediction_client.post(
            "/predict",
            json={
                "genomic_data": test_patient["genomic_data"],
                "medical_history": test_patient["medical_history"]
            }
        )
        assert pred_response.status_code == 200

@pytest.mark.slow
class TestSystemPerformance:
    """System-wide performance tests"""
    
    def test_response_times(
        self,
        patient_management_client: TestClient,
        treatment_prediction_client: TestClient,
        data_ingestion_client: TestClient,
        test_patient: Dict[str, Any]
    ):
        """Test response times under normal load"""
        # Measure ingestion time
        start_time = time.time()
        ingest_response = data_ingestion_client.post(
            "/ingest/patient",
            json=test_patient
        )
        ingest_time = time.time() - start_time
        assert ingest_time < 1.0  # Should take less than 1 second
        
        # Measure retrieval time
        start_time = time.time()
        get_response = patient_management_client.get(
            f"/patients/{test_patient['id']}"
        )
        retrieval_time = time.time() - start_time
        assert retrieval_time < 0.5  # Should take less than 0.5 seconds
        
        # Measure prediction time
        start_time = time.time()
        pred_response = treatment_prediction_client.post(
            "/predict",
            json={
                "genomic_data": test_patient["genomic_data"],
                "medical_history": test_patient["medical_history"]
            }
        )
        prediction_time = time.time() - start_time
        assert prediction_time < 2.0  # Should take less than 2 seconds
    
    def test_concurrent_operations(
        self,
        patient_management_client: TestClient,
        treatment_prediction_client: TestClient,
        data_ingestion_client: TestClient
    ):
        """Test system performance under concurrent operations"""
        test_patients = generate_test_patients(20)
        
        async def run_concurrent_operations():
            tasks = []
            # Ingestion tasks
            for patient in test_patients:
                task = asyncio.create_task(
                    data_ingestion_client.post(
                        "/ingest/patient",
                        json=patient
                    )
                )
                tasks.append(task)
            
            # Retrieval tasks
            for patient in test_patients[:10]:  # Use first 10 patients
                task = asyncio.create_task(
                    patient_management_client.get(
                        f"/patients/{patient['id']}"
                    )
                )
                tasks.append(task)
            
            # Prediction tasks
            for patient in test_patients[:5]:  # Use first 5 patients
                task = asyncio.create_task(
                    treatment_prediction_client.post(
                        "/predict",
                        json={
                            "genomic_data": patient["genomic_data"],
                            "medical_history": patient["medical_history"]
                        }
                    )
                )
                tasks.append(task)
            
            start_time = time.time()
            responses = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            return responses, total_time
        
        responses, total_time = asyncio.run(run_concurrent_operations())
        
        # Verify all operations succeeded
        assert all(r.status_code == 200 for r in responses)
        
        # Check total time is reasonable
        assert total_time < 10.0  # Should complete within 10 seconds
