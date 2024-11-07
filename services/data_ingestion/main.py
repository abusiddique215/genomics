from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import logging
import json
import boto3
from typing import Dict, Any, List
from decimal import Decimal
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb', endpoint_url='http://localhost:8000')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Patient(BaseModel):
    id: str
    name: str
    age: str
    genomic_data: Dict[str, Any]
    medical_history: Dict[str, Any]

class BatchPatientsRequest(BaseModel):
    patients: List[Patient]

def convert_to_dynamodb_item(patient: Dict[str, Any]) -> Dict[str, Any]:
    """Convert patient data to DynamoDB format"""
    return {
        'id': {'S': patient['id']},
        'name': {'S': patient['name']},
        'age': {'S': str(patient['age'])},
        'genomic_data': {
            'M': {
                'gene_variants': {'M': {k: {'S': str(v)} for k, v in patient['genomic_data']['gene_variants'].items()}},
                'mutation_scores': {'M': {k: {'S': str(v)} for k, v in patient['genomic_data']['mutation_scores'].items()}},
                'sequencing_quality': {'S': str(patient['genomic_data']['sequencing_quality'])}
            }
        },
        'medical_history': {
            'M': {
                'conditions': {'L': [{'S': str(c)} for c in patient['medical_history']['conditions']]},
                'treatments': {'L': [{'S': str(t)} for t in patient['medical_history']['treatments']]},
                'medications': {'L': [{'S': str(m)} for m in patient['medical_history']['medications']]},
                'allergies': {'L': [{'S': str(a)} for a in patient['medical_history']['allergies']]}
            }
        }
    }

@app.get("/")
async def root():
    """Root endpoint"""
    logger.debug("Root endpoint called")
    return {"message": "Data Ingestion Service"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check endpoint called")
    return {"status": "healthy"}

@app.post("/ingest/patient")
async def ingest_patient(patient: Patient):
    """Ingest a single patient"""
    try:
        logger.debug(f"Processing patient: {patient.id}")
        
        # Convert patient data to DynamoDB format
        item = convert_to_dynamodb_item(patient.dict())
        
        # Store in DynamoDB
        dynamodb.put_item(
            TableName='patients',
            Item=item
        )
        
        logger.info(f"Successfully ingested patient {patient.id}")
        return {
            "message": "Patient ingested successfully",
            "patient_id": patient.id
        }
        
    except Exception as e:
        logger.error(f"Error ingesting patient: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/patients/batch")
async def ingest_patients_batch(request: BatchPatientsRequest):
    """Ingest multiple patients"""
    try:
        logger.debug(f"Processing {len(request.patients)} patients")
        
        success_count = 0
        failed_patients = []
        
        for patient in request.patients:
            try:
                # Convert patient data to DynamoDB format
                item = convert_to_dynamodb_item(patient.dict())
                
                # Store in DynamoDB
                dynamodb.put_item(
                    TableName='patients',
                    Item=item
                )
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error ingesting patient {patient.id}: {str(e)}")
                failed_patients.append({
                    "patient_id": patient.id,
                    "error": str(e)
                })
        
        logger.info(f"Successfully ingested {success_count} patients")
        return {
            "message": "Batch ingestion completed",
            "success_count": success_count,
            "failed_count": len(failed_patients),
            "failed_patients": failed_patients
        }
        
    except Exception as e:
        logger.error(f"Error in batch ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/file")
async def ingest_file(file: UploadFile = File(...)):
    """Ingest patient data from file"""
    try:
        logger.debug(f"Processing file: {file.filename}")
        content = await file.read()
        content_str = content.decode()
        
        # Parse JSON data
        patients_data = json.loads(content_str)
        if not isinstance(patients_data, list):
            patients_data = [patients_data]
        
        success_count = 0
        failed_patients = []
        
        for patient_data in patients_data:
            try:
                # Convert patient data to DynamoDB format
                item = convert_to_dynamodb_item(patient_data)
                
                # Store in DynamoDB
                dynamodb.put_item(
                    TableName='patients',
                    Item=item
                )
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error ingesting patient {patient_data.get('id', 'unknown')}: {str(e)}")
                failed_patients.append({
                    "patient_id": patient_data.get('id', 'unknown'),
                    "error": str(e)
                })
        
        logger.info(f"Successfully processed {success_count} patients from file")
        return {
            "message": "File ingestion completed",
            "success_count": success_count,
            "failed_count": len(failed_patients),
            "failed_patients": failed_patients
        }
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)
