from fastapi.testclient import TestClient
from services.data_ingestion.main import app

client = TestClient(app)

def test_ingest_data():
    response = client.post("/ingest/", files={"file": ("test.csv", b"test,data\n1,2\n3,4")})
    assert response.status_code == 200
    assert response.json() == {"message": "Data ingested successfully"}