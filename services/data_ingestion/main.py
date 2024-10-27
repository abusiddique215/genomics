from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import logging
import json
from typing import Dict, Any
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.post("/ingest/genomics")
async def ingest_genomics_data(file: UploadFile = File(...)):
    """Ingest genomics data file"""
    try:
        logger.debug(f"Processing file: {file.filename}")
        content = await file.read()
        content_str = content.decode()
        
        # Process CSV data
        df = pd.read_csv(pd.StringIO(content_str))
        
        # Basic data validation
        required_columns = ['gene_id', 'variant']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Convert to dictionary format
        processed_data = df.to_dict(orient='records')
        
        logger.info(f"Successfully processed {len(processed_data)} records")
        return {
            "message": "Data ingested successfully",
            "record_count": len(processed_data)
        }
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/medical-history")
async def ingest_medical_history(data: Dict[str, Any]):
    """Ingest medical history data"""
    try:
        logger.debug(f"Processing medical history: {json.dumps(data, indent=2)}")
        
        # Basic data validation
        required_fields = ['patient_id', 'conditions', 'treatments']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        logger.info(f"Successfully processed medical history for patient {data['patient_id']}")
        return {
            "message": "Medical history ingested successfully",
            "patient_id": data['patient_id']
        }
        
    except Exception as e:
        logger.error(f"Error processing medical history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)
