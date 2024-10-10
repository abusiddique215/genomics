from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tensorflow as tf
import boto3
import numpy as np
from services.utils.logging import setup_logging

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

s3 = boto3.client('s3')

class PatientData(BaseModel):
    features: list[float]

@app.post("/predict/{model_name}")
async def predict_treatment(model_name: str, patient: PatientData):
    try:
        # Download model from S3
        bucket_name = 'your-s3-bucket-name'
        model_path = f'/tmp/{model_name}.h5'
        s3.download_file(bucket_name, f'models/{model_name}.h5', model_path)
        
        # Load the model
        model = tf.keras.models.load_model(model_path)
        
        # Make prediction
        input_data = np.array(patient.features).reshape(1, -1)
        prediction = model.predict(input_data)
        
        logger.info(f"Prediction made for model: {model_name}")
        return {"treatment_efficacy": float(prediction[0][0])}
    except Exception as e:
        logger.error(f"Error making prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))