import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
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

POWER_BI_API_URL = "https://api.powerbi.com/v1.0/myorg"
POWER_BI_DATASET_ID = os.getenv("POWER_BI_DATASET_ID")
POWER_BI_TABLE_NAME = os.getenv("POWER_BI_TABLE_NAME")
POWER_BI_ACCESS_TOKEN = os.getenv("POWER_BI_ACCESS_TOKEN")

class PowerBIData(BaseModel):
    rows: list

@app.post("/update-powerbi")
async def update_powerbi(data: PowerBIData):
    try:
        url = f"{POWER_BI_API_URL}/datasets/{POWER_BI_DATASET_ID}/tables/{POWER_BI_TABLE_NAME}/rows"
        headers = {
            "Authorization": f"Bearer {POWER_BI_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers, json=data.dict())
        
        if response.status_code == 200:
            logger.info("Data successfully sent to Power BI")
            return {"message": "Data updated in Power BI successfully"}
        else:
            logger.error(f"Failed to update Power BI: {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Failed to update Power BI")
    except Exception as e:
        logger.error(f"Error updating Power BI: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))