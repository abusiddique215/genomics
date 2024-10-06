from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from services.logging.logger import log_event, log_error

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Patients')

class PatientData(BaseModel):
    id: str
    medical_history: dict
    genomic_data: dict

@app.post("/patient")
async def create_patient(patient: PatientData):
    try:
        response = table.put_item(Item=patient.dict())
        log_event("patient_created", {"patient_id": patient.id})
        return {"message": "Patient data created successfully"}
    except ClientError as e:
        log_error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient/{patient_id}")
async def get_patient(patient_id: str):
    try:
        response = table.get_item(Key={'id': patient_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Patient not found")
        log_event("patient_retrieved", {"patient_id": patient_id})
        return response['Item']
    except ClientError as e:
        log_error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/patient/{patient_id}")
async def update_patient(patient_id: str, patient: PatientData):
    try:
        response = table.update_item(
            Key={'id': patient_id},
            UpdateExpression="set medical_history=:mh, genomic_data=:gd",
            ExpressionAttributeValues={
                ':mh': patient.medical_history,
                ':gd': patient.genomic_data
            },
            ReturnValues="UPDATED_NEW"
        )
        log_event("patient_updated", {"patient_id": patient_id})
        return {"message": "Patient data updated successfully"}
    except ClientError as e:
        log_error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

def log_patient_update(patient_id, action):
    # Implement logging logic for patient updates
    pass

def log_error(error_message):
    # Implement error logging logic
    pass