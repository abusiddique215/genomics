from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
import logging
import boto3
from datetime import datetime
import json
from .progress_tracker import ProgressTracker

app = FastAPI()
logger = logging.getLogger(__name__)
progress_tracker = ProgressTracker()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dynamodb = boto3.resource('dynamodb')
patient_table = dynamodb.Table('patients')

@app.post("/patient")
async def create_patient(patient: Dict):
    """Create a new patient record"""
    try:
        patient_table.put_item(Item=patient)
        logger.info(f"Created patient record: {patient['id']}")
        return {"message": "Patient created successfully"}
    except Exception as e:
        logger.error(f"Error creating patient: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient/{patient_id}")
async def get_patient(patient_id: str):
    """Get patient record by ID"""
    try:
        response = patient_table.get_item(Key={'id': patient_id})
        patient = response.get('Item')
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        logger.info(f"Patient retrieved: {patient_id}")
        return patient
    except Exception as e:
        logger.error(f"Error retrieving patient: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient")
async def list_patients():
    """List all patients"""
    try:
        response = patient_table.scan()
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error listing patients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/patient/{patient_id}/progress")
async def add_progress(patient_id: str, progress_data: Dict):
    """Add a progress entry for a patient"""
    try:
        result = progress_tracker.add_progress_entry(patient_id, progress_data)
        return result
    except Exception as e:
        logger.error(f"Error adding progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient/{patient_id}/progress")
async def get_progress(patient_id: str, start_date: Optional[str] = None):
    """Get progress history for a patient"""
    try:
        progress = progress_tracker.get_patient_progress(patient_id, start_date)
        return progress
    except Exception as e:
        logger.error(f"Error retrieving progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient/{patient_id}/progress/analysis")
async def analyze_patient_progress(patient_id: str):
    """Get analysis of patient's treatment progress"""
    try:
        analysis = progress_tracker.analyze_progress(patient_id)
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient/{patient_id}/treatment_recommendation")
async def get_treatment_recommendation(patient_id: str):
    """Get treatment recommendation for a patient"""
    try:
        # Get patient data
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
    uvicorn.run(app, host="0.0.0.0", port=8501)
