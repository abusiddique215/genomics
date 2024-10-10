from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import boto3
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

@app.post("/preprocess/{file_name}")
async def preprocess_data(file_name: str):
    try:
        # Download file from S3
        bucket_name = 'your-s3-bucket-name'
        response = s3.get_object(Bucket=bucket_name, Key=f'raw_data/{file_name}')
        df = pd.read_csv(response['Body'])
        
        # Perform preprocessing steps
        # Example: Remove rows with missing values
        df = df.dropna()
        
        # Example: Normalize numerical columns
        numerical_columns = df.select_dtypes(include=['float64', 'int64']).columns
        df[numerical_columns] = (df[numerical_columns] - df[numerical_columns].mean()) / df[numerical_columns].std()
        
        # Save preprocessed data back to S3
        preprocessed_file_name = f'preprocessed_data/{file_name}'
        s3.put_object(Bucket=bucket_name, Key=preprocessed_file_name, Body=df.to_csv(index=False))
        
        logger.info(f"Preprocessed file: {file_name}")
        return {"message": "Data preprocessed successfully"}
    except Exception as e:
        logger.error(f"Error preprocessing data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))