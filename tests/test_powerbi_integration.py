from fastapi.testclient import TestClient
from services.powerbi_integration.main import app
import pytest

client = TestClient(app)

def test_update_powerbi():
    test_data = {
        "rows": [
            {"id": "1", "name": "Test Patient", "age": 30}
        ]
    }
    response = client.post("/update-powerbi", json=test_data)
    assert response.status_code == 200
    assert response.json() == {"message": "Data updated in Power BI successfully"}

def test_update_powerbi_error():
    # Test with invalid data
    test_data = {"invalid": "data"}
    response = client.post("/update-powerbi", json=test_data)
    assert response.status_code == 422  # Unprocessable Entity