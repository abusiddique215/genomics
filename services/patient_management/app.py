from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from botocore.exceptions import ClientError
import logging
import requests
from services.utils.logging import setup_logging
from services.utils.error_handling import (
    validate_patient_data,
    handle_error,
    ValidationError,
    DatabaseError
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Starting patient_management app.py")

logger.debug("Creating FastAPI application")
app = FastAPI()

logger.debug("Adding CORS middleware")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PatientData(BaseModel):
    id: str
    name: str
    age: int
    genomic_data: dict
    medical_history: dict

    @validator('age')
    def validate_age(cls, v):
        if v < 0 or v > 150:
            raise ValueError('Age must be between 0 and 150')
        return v

    @validator('name')
    def validate_name(cls, v):
        if len(v) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return v

# Placeholder for patient data storage
patients = {}

TREATMENT_PREDICTION_URL = "http://localhost:8083"

@app.on_event("startup")
async def startup_event():
    logger.debug("FastAPI application is starting up")

@app.get("/")
async def root():
    logger.debug("Handling GET request to /")
    return {"message": "Patient Management Service is running"}

@app.post("/patient")
async def create_patient(patient: PatientData):
    logger.debug(f"Handling POST request to /patient with data: {patient}")
    try:
        # Validate patient data
        validate_patient_data(patient.dict())
        
        # Store patient data
        patients[patient.id] = patient.dict()
        logger.info(f"Patient created: {patient.id}")
        return {"message": "Patient created successfully"}
    except Exception as e:
        return handle_error(e)

@app.get("/patient")
async def get_all_patients():
    logger.debug("Handling GET request to /patient")
    try:
        return list(patients.values())
    except Exception as e:
        return handle_error(e)

@app.get("/patient/{patient_id}")
async def get_patient(patient_id: str):
    logger.debug(f"Handling GET request to /patient/{patient_id}")
    try:
        if patient_id not in patients:
            raise ValidationError("Patient not found", "patient_id")
        logger.info(f"Patient retrieved: {patient_id}")
        return patients[patient_id]
    except Exception as e:
        return handle_error(e)

@app.put("/patient/{patient_id}")
async def update_patient(patient_id: str, patient: PatientData):
    logger.debug(f"Handling PUT request to /patient/{patient_id} with data: {patient}")
    try:
        if patient_id not in patients:
            raise ValidationError("Patient not found", "patient_id")
        
        # Validate patient data
        validate_patient_data(patient.dict())
        
        # Update patient data
        patients[patient_id] = patient.dict()
        logger.info(f"Patient updated: {patient_id}")
        return {"message": "Patient updated successfully"}
    except Exception as e:
        return handle_error(e)

@app.get("/patient/{patient_id}/treatment_recommendation")
async def get_treatment_recommendation(patient_id: str):
    logger.debug(f"Handling GET request to /patient/{patient_id}/treatment_recommendation")
    try:
        if patient_id not in patients:
            raise ValidationError("Patient not found", "patient_id")
        
        patient = patients[patient_id]
        try:
            response = requests.post(f"{TREATMENT_PREDICTION_URL}/predict", json={
                "id": patient["id"],
                "genomic_data": patient["genomic_data"],
                "medical_history": patient["medical_history"]
            })
            response.raise_for_status()
            recommendation = response.json()
            logger.info(f"Treatment recommendation received for patient {patient_id}")
            return recommendation
        except requests.RequestException as e:
            raise DatabaseError(f"Error getting treatment recommendation: {str(e)}")
    except Exception as e:
        return handle_error(e)

logger.debug("FastAPI application setup completed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)
