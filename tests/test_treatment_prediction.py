import pytest
from fastapi.testclient import TestClient
from .utils import (
    generate_test_patient,
    assert_valid_treatment_recommendation
)

@pytest.mark.integration
class TestTreatmentPredictionAPI:
    """Integration tests for Treatment Prediction API"""
    
    def test_predict_treatment(self, treatment_prediction_client: TestClient, test_patient):
        """Test treatment prediction"""
        response = treatment_prediction_client.post(
            "/predict",
            json={
                "genomic_data": test_patient["genomic_data"],
                "medical_history": test_patient["medical_history"]
            }
        )
        assert response.status_code == 200
        prediction = response.json()
        assert_valid_treatment_recommendation(prediction)
    
    def test_batch_prediction(self, treatment_prediction_client: TestClient):
        """Test batch treatment prediction"""
        patients = [generate_test_patient() for _ in range(3)]
        predictions = []
        
        for patient in patients:
            response = treatment_prediction_client.post(
                "/predict",
                json={
                    "genomic_data": patient["genomic_data"],
                    "medical_history": patient["medical_history"]
                }
            )
            assert response.status_code == 200
            prediction = response.json()
            assert_valid_treatment_recommendation(prediction)
            predictions.append(prediction)
        
        # Verify predictions are different
        treatments = [p["recommended_treatment"] for p in predictions]
        assert len(set(treatments)) > 1  # At least some variation
    
    def test_invalid_input(self, treatment_prediction_client: TestClient):
        """Test handling of invalid input"""
        response = treatment_prediction_client.post(
            "/predict",
            json={"invalid": "data"}
        )
        assert response.status_code == 422

@pytest.mark.unit
class TestTreatmentPredictionUnit:
    """Unit tests for Treatment Prediction service"""
    
    def test_model_prediction(self, mock_ai_model, test_patient):
        """Test AI model prediction"""
        prediction = mock_ai_model.predict({
            "genomic_data": test_patient["genomic_data"],
            "medical_history": test_patient["medical_history"]
        })
        assert_valid_treatment_recommendation(prediction)
    
    def test_data_preprocessing(self, test_patient):
        """Test data preprocessing"""
        from services.treatment_prediction.main import preprocess_data
        
        processed = preprocess_data({
            "genomic_data": test_patient["genomic_data"],
            "medical_history": test_patient["medical_history"]
        })
        
        assert "features" in processed
        assert isinstance(processed["features"], list)
    
    def test_confidence_calculation(self):
        """Test confidence level calculation"""
        from services.treatment_prediction.main import calculate_confidence
        
        assert calculate_confidence(0.9) == "high"
        assert calculate_confidence(0.7) == "medium"
        assert calculate_confidence(0.4) == "low"

@pytest.mark.slow
class TestTreatmentPredictionPerformance:
    """Performance tests for Treatment Prediction service"""
    
    def test_prediction_latency(self, treatment_prediction_client: TestClient, test_patient):
        """Test prediction latency"""
        import time
        
        start_time = time.time()
        response = treatment_prediction_client.post(
            "/predict",
            json={
                "genomic_data": test_patient["genomic_data"],
                "medical_history": test_patient["medical_history"]
            }
        )
        duration = time.time() - start_time
        
        assert response.status_code == 200
        assert duration < 1.0  # Should respond within 1 second
    
    def test_model_memory_usage(self, mock_ai_model):
        """Test model memory usage"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Make multiple predictions
        for _ in range(100):
            mock_ai_model.predict({"test": "data"})
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 100 * 1024 * 1024  # Less than 100MB
