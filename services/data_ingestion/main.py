from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from Bio import SeqIO
from io import StringIO
import logging
import boto3
import os
from typing import List, Dict, Any

app = FastAPI()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

s3 = boto3.client('s3')
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

def process_csv(content: str) -> pd.DataFrame:
    """Process CSV format genomics data"""
    try:
        df = pd.read_csv(StringIO(content))
        # Handle missing values
        df = df.fillna(df.mean() if df.select_dtypes(include=[np.number]).columns.any() else 'unknown')
        return df
    except Exception as e:
        logger.error(f"Error processing CSV: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")

def process_fasta(content: str) -> Dict[str, Any]:
    """Process FASTA format genomics data"""
    try:
        sequences = {}
        for record in SeqIO.parse(StringIO(content), "fasta"):
            sequences[record.id] = {
                'sequence': str(record.seq),
                'description': record.description
            }
        return sequences
    except Exception as e:
        logger.error(f"Error processing FASTA: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing FASTA: {str(e)}")

@app.post("/ingest/genomics")
async def ingest_genomics_data(file: UploadFile = File(...)):
    """Ingest genomics data in CSV or FASTA format"""
    try:
        content = await file.read()
        content_str = content.decode()
        
        # Determine file type and process accordingly
        if file.filename.endswith('.csv'):
            processed_data = process_csv(content_str)
            file_type = 'csv'
        elif file.filename.endswith(('.fasta', '.fa')):
            processed_data = process_fasta(content_str)
            file_type = 'fasta'
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Store processed data
        processed_key = f"processed/{file.filename}"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=processed_key,
            Body=str(processed_data).encode()
        )
        
        # Log ingestion event
        logger.info(f"Ingested {file_type} file: {file.filename}")
        
        return {
            "message": "Data ingested successfully",
            "file_type": file_type,
            "processed_location": processed_key
        }
    except Exception as e:
        logger.error(f"Error ingesting data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/medical-history")
async def ingest_medical_history(
    patient_id: str,
    medical_history: Dict[str, Any]
):
    """Ingest patient medical history"""
    try:
        # Store medical history
        key = f"medical_history/{patient_id}.json"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=str(medical_history).encode()
        )
        
        logger.info(f"Ingested medical history for patient: {patient_id}")
        
        return {
            "message": "Medical history ingested successfully",
            "patient_id": patient_id,
            "storage_location": key
        }
    except Exception as e:
        logger.error(f"Error ingesting medical history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/status")
async def get_data_status():
    """Get status of ingested data"""
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        files = [obj['Key'] for obj in response.get('Contents', [])]
        
        return {
            "total_files": len(files),
            "genomics_files": len([f for f in files if f.startswith('processed/')]),
            "medical_history_files": len([f for f in files if f.startswith('medical_history/')])
        }
    except Exception as e:
        logger.error(f"Error getting data status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)
