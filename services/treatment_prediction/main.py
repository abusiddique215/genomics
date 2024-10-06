from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tensorflow as tf
import boto3
import numpy as np
from pydantic import BaseModel
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

s3 = boto3.client('s3')

class PatientData(BaseModel):
    id: str
    features: list[float]

@app.post("/predict")
async def predict_treatment(patient_data: PatientData):
    try:
        model = load_latest_model()
        input_data = np.array(patient_data.features).reshape(1, -1)
        
        prediction = model.predict(input_data)
        
        treatment_recommendations = process_prediction(prediction)
        
        log_event("treatment_prediction", {
            "patient_id": patient_data.id,
            "prediction": prediction.tolist(),
            "recommendations": treatment_recommendations
        })
        
        return {"recommendations": treatment_recommendations}
    except Exception as e:
        log_error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

def load_latest_model():
    # Get the latest model file from S3
    response = s3.list_objects_v2(Bucket='genomics-models', Prefix='model_')
    latest_model = max(response['Contents'], key=lambda x: x['LastModified'])
    
    # Download the model file
    s3.download_file('genomics-models', latest_model['Key'], 'latest_model.h5')
    
    # Load the model
    return tf.keras.models.load_model('latest_model.h5')

def process_prediction(prediction):
    # Convert prediction to treatment recommendations
    threshold = 0.5
    if prediction[0][0] > threshold:
        return {"treatment": "Treatment A", "efficacy": "High"}
    else:
        return {"treatment": "Treatment B", "efficacy": "Medium"}