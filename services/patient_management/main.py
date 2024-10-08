from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from services.utils.logging import setup_logging
import requests
import os

app = FastAPI()
logger = setup_logging()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AWS DynamoDB client
try:
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Patients')
except Exception as e:
    logger.error(f"Failed to initialize DynamoDB: {str(e)}")
    raise

# RAG pipeline service URL
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:8006")

class PatientData(BaseModel):
    id: str
    name: str
    age: int
    genomic_data: dict
    medical_history: dict

@app.post("/patient")
async def create_patient(patient: PatientData):
    try:
        response = table.put_item(Item=patient.dict())
        logger.info(f"Patient created: {patient.id}")
        
        # Trigger RAG pipeline update
        await update_rag_pipeline()
        
        return {"message": "Patient created successfully"}
    except ClientError as e:
        logger.error(f"Error creating patient: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient/{patient_id}")
async def get_patient(patient_id: str):
    try:
        response = table.get_item(Key={'id': patient_id})
        if 'Item' not in response:
            logger.warning(f"Patient not found: {patient_id}")
            raise HTTPException(status_code=404, detail="Patient not found")
        logger.info(f"Patient retrieved: {patient_id}")
        return response['Item']
    except ClientError as e:
        logger.error(f"Error retrieving patient: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/patient/{patient_id}")
async def update_patient(patient_id: str, patient: PatientData):
    try:
        response = table.update_item(
            Key={'id': patient_id},
            UpdateExpression="set name=:n, age=:a, genomic_data=:g, medical_history=:m",
            ExpressionAttributeValues={
                ':n': patient.name,
                ':a': patient.age,
                ':g': patient.genomic_data,
                ':m': patient.medical_history
            },
            ReturnValues="UPDATED_NEW"
        )
        logger.info(f"Patient updated: {patient_id}")
        
        # Trigger RAG pipeline update
        await update_rag_pipeline()
        
        return {"message": "Patient updated successfully"}
    except ClientError as e:
        logger.error(f"Error updating patient: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def update_rag_pipeline():
    try:
        response = requests.post(f"{RAG_SERVICE_URL}/update_patient_data")
        if response.status_code != 200:
            logger.error(f"Failed to update RAG pipeline: {response.text}")
        else:
            logger.info("RAG pipeline updated successfully")
    except Exception as e:
        logger.error(f"Error updating RAG pipeline: {str(e)}")

@app.get("/test-aws-connection")
async def test_aws_connection():
    try:
        # Test DynamoDB connection
        table.scan(Limit=1)

        # Test S3 connection
        s3 = boto3.client('s3')
        s3.list_buckets()

        return {"message": "AWS connection successful"}
    except ClientError as e:
        logger.error(f"AWS connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AWS connection error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)