from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import logging
from typing import Dict, Any
import sys
import os
from pydantic import BaseModel, Field
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_model.model import GenomicsTreatmentModel

app = FastAPI(
    title="Genomics Treatment Prediction API",
    description="API for predicting treatment recommendations based on genomic data",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize the model
model = GenomicsTreatmentModel()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictionRequest(BaseModel):
    genomic_data: Dict[str, Any] = Field(
        ...,
        description="Patient's genomic data including variants and mutations"
    )
    medical_history: Dict[str, Any] = Field(
        ...,
        description="Patient's medical history including conditions and treatments"
    )

class PredictionResponse(BaseModel):
    recommended_treatment: str = Field(
        ...,
        description="Recommended treatment based on analysis"
    )
    efficacy: float = Field(
        ...,
        ge=0,
        le=1,
        description="Predicted efficacy score (0-1)"
    )
    confidence_level: str = Field(
        ...,
        description="Confidence level of the prediction (high/medium/low)"
    )

@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict_treatment(patient_data: PredictionRequest):
    """
    Predict treatment based on patient genomic and medical data.
    
    The model analyzes the patient's genomic data and medical history to recommend
    the most effective treatment option.
    
    - **genomic_data**: Dictionary containing genomic markers and variants
    - **medical_history**: Dictionary containing medical conditions and previous treatments
    
    Returns a prediction including:
    - Recommended treatment
    - Predicted efficacy score (0-1)
    - Confidence level of the prediction
    """
    try:
        # Preprocess data
        processed_data = model.preprocess_data(
            patient_data.genomic_data,
            patient_data.medical_history
        )
        
        # Get prediction
        treatment, efficacy = model.predict_treatment(processed_data)
        
        logger.info(f"Recommending {treatment} with efficacy {efficacy:.2f}")
        
        return {
            "recommended_treatment": treatment,
            "efficacy": efficacy,
            "confidence_level": "high" if efficacy > 0.8 else "medium" if efficacy > 0.6 else "low"
        }
        
    except Exception as e:
        logger.error(f"Error predicting treatment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)
