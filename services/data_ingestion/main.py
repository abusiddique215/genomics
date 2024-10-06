from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import boto3
from botocore.exceptions import ClientError
from services.logging.logger import log_event, log_error
import io
from Bio import SeqIO

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

@app.post("/ingest")
async def ingest_data(file: UploadFile = File(...)):
    try:
        # Read the file content
        content = await file.read()
        
        # Determine file type and preprocess accordingly
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        elif file.filename.endswith('.fasta'):
            records = list(SeqIO.parse(io.StringIO(content.decode('utf-8')), "fasta"))
            df = pd.DataFrame([(rec.id, str(rec.seq)) for rec in records], columns=['id', 'sequence'])
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Preprocess the data (implement your preprocessing steps here)
        preprocessed_data = preprocess_data(df)
        
        # Save preprocessed data to S3
        s3.put_object(Bucket='genomics-data', Key=f'preprocessed/{file.filename}', Body=preprocessed_data.to_csv(index=False))
        
        # Log the ingestion event
        log_event("data_ingestion", {"filename": file.filename, "size": len(content), "preprocessing": "completed"})
        
        return {"message": "Data ingested and preprocessed successfully"}
    except Exception as e:
        log_error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

def preprocess_data(df):
    # Handle missing values
    df = df.fillna(df.mean())
    
    # Normalize numerical columns
    numerical_columns = df.select_dtypes(include=['float64', 'int64']).columns
    df[numerical_columns] = (df[numerical_columns] - df[numerical_columns].mean()) / df[numerical_columns].std()
    
    # Perform feature extraction (example: PCA)
    # from sklearn.decomposition import PCA
    # pca = PCA(n_components=10)
    # df_pca = pd.DataFrame(pca.fit_transform(df[numerical_columns]))
    # df = pd.concat([df, df_pca], axis=1)
    
    return df