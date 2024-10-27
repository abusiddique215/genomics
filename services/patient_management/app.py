from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import boto3
from typing import Dict, Optional
from datetime import datetime
import json
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb',
                         endpoint_url='http://localhost:8000',
                         region_name='us-west-2',
                         aws_access_key_id='dummy',
                         aws_secret_access_key='dummy')
patient_table = dynamodb.Table('patients')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

def convert_decimals(obj):
    """Convert Decimal objects to strings"""
    return json.loads(json.dumps(obj, cls=DecimalEncoder))

@app.get("/")
async def root():
    """Root endpoint"""
    logger.debug("Root endpoint called")
    return {"message": "Patient Management Service"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check endpoint called")
    try:
        # Test DynamoDB connection
        patient_table.get_item(Key={'id': 'test'})
        logger.info("Health check successful")
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}

@app.post("/patients")
async def create_patient(patient: Dict):
    """Create a new patient record"""
    try:
        logger.debug(f"Creating patient: {json.dumps(patient, indent=2)}")
        
        # Store in DynamoDB
        patient_table.put_item(Item=patient)
        logger.info(f"Created patient record: {patient['id']}")
        return {"message": "Patient created successfully"}
    except Exception as e:
        logger.error(f"Error creating patient: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patients/{patient_id}")
async def get_patient(patient_id: str):
    """Get patient record by ID"""
    try:
        logger.debug(f"Getting patient: {patient_id}")
        response = patient_table.get_item(Key={'id': patient_id})
        patient = response.get('Item')
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        logger.info(f"Retrieved patient: {patient_id}")
        return convert_decimals(patient)
    except Exception as e:
        logger.error(f"Error retrieving patient: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patients")
async def list_patients():
    """List all patients"""
    try:
        logger.debug("Listing all patients")
        response = patient_table.scan()
        patients = response.get('Items', [])
        logger.info(f"Retrieved {len(patients)} patients")
        return convert_decimals(patients)
    except Exception as e:
        logger.error(f"Error listing patients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patients/{patient_id}/treatment_recommendation")
async def get_treatment_recommendation(patient_id: str):
    """Get treatment recommendation for a patient"""
    try:
        # Get patient data
        logger.debug(f"Getting treatment recommendation for patient: {patient_id}")
        patient = await get_patient(patient_id)
        
        # Get treatment prediction from prediction service
        import requests
        response = requests.post(
            "http://localhost:8083/predict",
            json={
                "genomic_data": patient.get("genomic_data", {}),
                "medical_history": patient.get("medical_history", {})
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error getting treatment recommendation")
            
        recommendation = response.json()
        logger.info(f"Treatment recommendation received for patient {patient_id}")
        return recommendation
        
    except Exception as e:
        logger.error(f"Error getting treatment recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
