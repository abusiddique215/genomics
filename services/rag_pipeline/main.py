from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from services.utils.logging import setup_logging
import os

# Langchain imports
from langchain.llms import OpenAI
from langchain.chains import VectorDBQA
from langchain.document_loaders import S3FileLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter

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

# Initialize AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
patients_table = dynamodb.Table('Patients')

# Initialize OpenAI API
openai_api_key = os.getenv("OPENAI_API_KEY")
llm = OpenAI(temperature=0, openai_api_key=openai_api_key)

# Initialize vector store
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
vector_store = None

class Query(BaseModel):
    question: str

@app.on_event("startup")
async def startup_event():
    global vector_store
    try:
        # Load documents from S3
        bucket_name = os.getenv("S3_BUCKET_NAME")
        loader = S3FileLoader(bucket_name, "patient_data.txt")
        documents = loader.load()
        
        # Split documents
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)
        
        # Create vector store
        vector_store = FAISS.from_documents(texts, embeddings)
        logger.info("Vector store initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing vector store: {str(e)}")
        raise

@app.post("/query")
async def query_rag(query: Query):
    try:
        if not vector_store:
            raise HTTPException(status_code=500, detail="Vector store not initialized")
        
        qa = VectorDBQA.from_chain_type(llm=llm, chain_type="stuff", vectorstore=vector_store)
        result = qa.run(query.question)
        
        logger.info(f"RAG query processed: {query.question}")
        return {"answer": result}
    except Exception as e:
        logger.error(f"Error processing RAG query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update_patient_data")
async def update_patient_data():
    try:
        # Fetch all patient data from DynamoDB
        response = patients_table.scan()
        patients = response['Items']
        
        # Prepare data for S3
        patient_data = "\n".join([str(patient) for patient in patients])
        
        # Upload to S3
        bucket_name = os.getenv("S3_BUCKET_NAME")
        s3.put_object(Bucket=bucket_name, Key="patient_data.txt", Body=patient_data)
        
        # Reinitialize vector store
        global vector_store
        loader = S3FileLoader(bucket_name, "patient_data.txt")
        documents = loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)
        vector_store = FAISS.from_documents(texts, embeddings)
        
        logger.info("Patient data updated and vector store reinitialized")
        return {"message": "Patient data updated successfully"}
    except Exception as e:
        logger.error(f"Error updating patient data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)