from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tensorflow as tf
import boto3
import pandas as pd
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

def create_model(input_shape):
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(64, activation='relu', input_shape=(input_shape,)),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(16, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

@app.post("/train/{file_name}")
async def train_model(file_name: str):
    try:
        # Download preprocessed data from S3
        bucket_name = 'your-s3-bucket-name'
        response = s3.get_object(Bucket=bucket_name, Key=f'preprocessed_data/{file_name}')
        df = pd.read_csv(response['Body'])
        
        # Prepare data for training
        X = df.drop('target', axis=1)  # Assuming 'target' is the column to predict
        y = df['target']
        
        # Create and train the model
        model = create_model(input_shape=X.shape[1])
        history = model.fit(X, y, epochs=10, validation_split=0.2)
        
        # Save the trained model
        model_path = f'models/model_{file_name}.h5'
        model.save(model_path)
        s3.upload_file(model_path, bucket_name, f'models/{file_name}.h5')
        
        logger.info(f"Model trained and saved: {file_name}")
        return {"message": "Model trained successfully"}
    except Exception as e:
        logger.error(f"Error training model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))