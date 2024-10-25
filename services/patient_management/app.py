from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import boto3

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb',
                         endpoint_url='http://localhost:8000',
                         region_name='us-west-2',
                         aws_access_key_id='dummy',
                         aws_secret_access_key='dummy')
patient_table = dynamodb.Table('patients')

@app.get("/")
async def root():
    """Root endpoint"""
    logger.debug("Root endpoint called")
    return {"message": "Patient Management Service"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check endpoint called")
    try:
        # Test DynamoDB connection
        patient_table.get_item(Key={'id': 'test'})
        logger.info("Health check successful")
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
