from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import boto3
from services.utils.logging import setup_logging
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

s3 = boto3.client('s3')
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

@app.post("/ingest/")
async def ingest_data(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df = pd.read_csv(content)
        
        # Process and store the data in S3
        bucket_name = 'your-s3-bucket-name'
        file_name = f'raw_data/{file.filename}'
        s3.put_object(Bucket=bucket_name, Key=file_name, Body=content)
        
        logger.info(f"Ingested file: {file.filename}")
        return {"message": "Data ingested successfully"}
    except Exception as e:
        logger.error(f"Error ingesting data: {str(e)}")
        return {"error": str(e)}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        s3.upload_fileobj(file.file, BUCKET_NAME, file.filename)
        return {"message": f"File {file.filename} uploaded successfully"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/files/")
async def list_files():
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        files = [obj['Key'] for obj in response.get('Contents', [])]
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}