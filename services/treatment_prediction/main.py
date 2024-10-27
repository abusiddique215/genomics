from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import logging
from typing import Dict, Any
import sys
import os
from decimal import Decimal
import json

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
    return {"message": "Treatment Prediction Service"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check endpoint called")
    return {"status": "healthy"}

@app.post("/predict")
async def predict_treatment(patient_data: Dict[str, Any]):
    """Predict treatment based on patient data"""
    try:
        logger.debug(f"Received prediction request: {json.dumps(patient_data, indent=2)}")
        
        # Mock prediction logic
        treatments = ['Treatment A', 'Treatment B', 'Treatment C']
        treatment = np.random.choice(treatments)
        efficacy = float(np.random.uniform(0.6, 0.99))
        
        result = {
            "recommended_treatment": treatment,
            "efficacy": efficacy,
            "confidence_level": "high" if efficacy > 0.8 else "medium" if efficacy > 0.6 else "low"
        }
        
        logger.info(f"Generated prediction: {json.dumps(result, indent=2)}")
        return result
        
    except Exception as e:
        logger.error(f"Error generating prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)
