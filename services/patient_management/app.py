from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
import logging
import boto3
from datetime import datetime
import json
from .progress_tracker import ProgressTracker
from pydantic import BaseModel, Field
from enum import Enum

app = FastAPI(
    title="Genomics Treatment System API",
    description="API for managing patient data and treatment recommendations in the genomics system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

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

# Pydantic models for request/response validation
class TreatmentEfficacy(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class GenomicData(BaseModel):
    gene_variants: Dict[str, str] = Field(..., description="Dictionary of gene variants")
    mutation_scores: Dict[str, float] = Field(..., description="Dictionary of mutation scores")

class MedicalHistory(BaseModel):
    conditions: List[str] = Field(..., description="List of medical conditions")
    treatments: List[str] = Field(..., description="List of previous treatments")
    allergies: List[str] = Field(default=[], description="List of allergies")
    medications: List[str] = Field(default=[], description="List of current medications")

class Patient(BaseModel):
    id: str = Field(..., description="Unique patient identifier")
    name: str = Field(..., description="Patient's full name")
    age: int = Field(..., ge=0, le=150, description="Patient's age")
    genomic_data: GenomicData = Field(..., description="Patient's genomic data")
    medical_history: MedicalHistory = Field(..., description="Patient's medical history")

class ProgressEntry(BaseModel):
    treatment: str = Field(..., description="Treatment being administered")
    efficacy_score: float = Field(..., ge=0, le=1, description="Treatment efficacy score")
    side_effects: List[str] = Field(default=[], description="List of side effects")
    notes: str = Field(default="", description="Additional notes")
    metrics: Dict[str, float] = Field(default={}, description="Treatment metrics")
    next_appointment: str = Field(..., description="Next appointment date")

class TreatmentRecommendation(BaseModel):
    recommended_treatment: str = Field(..., description="Recommended treatment")
    efficacy: float = Field(..., ge=0, le=1, description="Predicted efficacy")
    confidence_level: TreatmentEfficacy = Field(..., description="Confidence level of prediction")

@app.post("/patient", response_model=Dict, tags=["Patient Management"])
async def create_patient(patient: Patient):
    """
    Create a new patient record with genomic data and medical history.
    
    - **patient**: Patient information including genomic data and medical history
    """
    try:
        patient_table.put_item(Item=patient.dict())
        logger.info(f"Created patient record: {patient.id}")
        return {"message": "Patient created successfully"}
    except Exception as e:
        logger.error(f"Error creating patient: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient/{patient_id}", response_model=Patient, tags=["Patient Management"])
async def get_patient(patient_id: str):
    """
    Retrieve a patient's record by their ID.
    
    - **patient_id**: Unique identifier of the patient
    """
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

@app.get("/patient", response_model=List[Patient], tags=["Patient Management"])
async def list_patients():
    """
    List all patients in the system.
    """
    try:
        response = patient_table.scan()
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error listing patients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/patient/{patient_id}/progress", response_model=ProgressEntry, tags=["Progress Tracking"])
async def add_progress(patient_id: str, progress_data: ProgressEntry):
    """
    Add a progress entry for a patient's treatment.
    
    - **patient_id**: Unique identifier of the patient
    - **progress_data**: Progress entry data including treatment efficacy and metrics
    """
    try:
        result = progress_tracker.add_progress_entry(patient_id, progress_data.dict())
        return result
    except Exception as e:
        logger.error(f"Error adding progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient/{patient_id}/progress", response_model=List[ProgressEntry], tags=["Progress Tracking"])
async def get_progress(
    patient_id: str,
    start_date: Optional[str] = Query(None, description="Filter entries from this date (ISO format)")
):
    """
    Get progress history for a patient.
    
    - **patient_id**: Unique identifier of the patient
    - **start_date**: Optional start date to filter progress entries
    """
    try:
        progress = progress_tracker.get_patient_progress(patient_id, start_date)
        return progress
    except Exception as e:
        logger.error(f"Error retrieving progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient/{patient_id}/treatment_recommendation", response_model=TreatmentRecommendation, tags=["Treatment"])
async def get_treatment_recommendation(patient_id: str):
    """
    Get treatment recommendation for a patient based on their genomic data and medical history.
    
    - **patient_id**: Unique identifier of the patient
    """
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
