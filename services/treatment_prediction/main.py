from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import logging
from typing import Dict, Any
import sys
import os
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_model.model import GenomicsTreatmentModel

app = FastAPI()
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

@app.post("/predict")
async def predict_treatment(patient_data: Dict[str, Any]):
    """Predict treatment based on patient genomic and medical data"""
    try:
        # Extract data
        genomic_data = patient_data.get('genomic_data', {})
        medical_history = patient_data.get('medical_history', {})
        
        # Preprocess data
        processed_data = model.preprocess_data(genomic_data, medical_history)
        
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

@app.post("/train")
async def train_model(training_data: Dict[str, Any]):
    """Train model with new data"""
    try:
        X_train = np.array(training_data['features'])
        y_train = np.array(training_data['labels'])
        
        history = model.train(X_train, y_train)
        
        return {
            "message": "Model training completed",
            "final_accuracy": float(history.history['accuracy'][-1]),
            "final_loss": float(history.history['loss'][-1])
        }
        
    except Exception as e:
        logger.error(f"Error training model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)
