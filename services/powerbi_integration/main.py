from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import requests
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

# Power BI API configuration
POWER_BI_API_URL = "https://api.powerbi.com/v1.0/myorg"
POWER_BI_DATASET_ID = "your_dataset_id"
ACCESS_TOKEN = "your_access_token"  # You should use a more secure way to store this

class DashboardData(BaseModel):
    data: dict

@app.post("/update_dashboard")
async def update_dashboard(data: DashboardData):
    try:
        # Convert data to DataFrame
        df = pd.DataFrame(data.data)
        
        # Update Power BI dataset
        response = update_powerbi_dataset(df)
        
        if response.status_code == 200:
            log_event("dashboard_update", {"status": "success"})
            return {"message": "Dashboard updated successfully"}
        else:
            log_error(f"Failed to update dashboard: {response.text}")
            raise HTTPException(status_code=500, detail="Failed to update dashboard")
    except Exception as e:
        log_error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_report")
async def generate_report(report_config: dict):
    try:
        # Generate report using Power BI API
        response = generate_powerbi_report(report_config)
        
        if response.status_code == 200:
            report_url = response.json().get('reportUrl')
            log_event("report_generation", {"status": "success", "report_url": report_url})
            return {"report_url": report_url}
        else:
            log_error(f"Failed to generate report: {response.text}")
            raise HTTPException(status_code=500, detail="Failed to generate report")
    except Exception as e:
        log_error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

def update_powerbi_dataset(df):
    url = f"{POWER_BI_API_URL}/datasets/{POWER_BI_DATASET_ID}/tables/YourTableName/rows"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = df.to_dict(orient='records')
    return requests.post(url, headers=headers, json={"rows": data})

def generate_powerbi_report(report_config):
    url = f"{POWER_BI_API_URL}/reports"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    return requests.post(url, headers=headers, json=report_config)