from typing import Dict, List, Optional, Any
import asyncio
import aiohttp
import logging
from datetime import datetime
from config import config
from .logging import get_logger

logger = get_logger('orchestration')

class ServiceOrchestrator:
    """Orchestrate service interactions and workflows"""
    
    def __init__(self):
        self.services = config.get('services', {})
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Create aiohttp session"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def check_service_health(self, service_url: str) -> bool:
        """Check if a service is healthy"""
        try:
            async with self.session.get(f"{service_url}/health") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Health check failed for {service_url}: {str(e)}")
            return False
    
    async def check_all_services(self) -> Dict[str, bool]:
        """Check health of all services"""
        results = {}
        for name, url in self.services.items():
            results[name] = await self.check_service_health(url)
        return results
    
    async def process_patient(
        self,
        patient_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process patient data through the complete workflow"""
        try:
            # 1. Ingest patient data
            async with self.session.post(
                f"{self.services['data_ingestion']}/ingest/patient",
                json=patient_data
            ) as response:
                if response.status != 200:
                    raise Exception("Data ingestion failed")
                ingestion_result = await response.json()
            
            # 2. Get treatment recommendation
            async with self.session.post(
                f"{self.services['treatment_prediction']}/predict",
                json={
                    "genomic_data": patient_data["genomic_data"],
                    "medical_history": patient_data["medical_history"]
                }
            ) as response:
                if response.status != 200:
                    raise Exception("Treatment prediction failed")
                prediction_result = await response.json()
            
            # 3. Update patient record
            async with self.session.post(
                f"{self.services['patient_management']}/patients/{patient_data['id']}/treatments",
                json={"treatment": prediction_result["recommended_treatment"]}
            ) as response:
                if response.status != 200:
                    raise Exception("Patient update failed")
            
            return {
                "status": "success",
                "patient_id": patient_data["id"],
                "recommendation": prediction_result,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Workflow failed for patient {patient_data['id']}: {str(e)}")
            raise
    
    async def batch_process_patients(
        self,
        patients: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process multiple patients concurrently"""
        tasks = []
        for patient in patients:
            task = asyncio.create_task(self.process_patient(patient))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = []
        failed = []
        
        for patient, result in zip(patients, results):
            if isinstance(result, Exception):
                failed.append({
                    "patient_id": patient["id"],
                    "error": str(result)
                })
            else:
                successful.append(result)
        
        return {
            "successful_count": len(successful),
            "failed_count": len(failed),
            "successful": successful,
            "failed": failed
        }
    
    async def retry_failed_operations(
        self,
        failed_operations: List[Dict[str, Any]],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Retry failed operations"""
        results = {
            "retried": [],
            "failed": []
        }
        
        for operation in failed_operations:
            patient_id = operation["patient_id"]
            retries = 0
            
            while retries < max_retries:
                try:
                    # Get patient data
                    async with self.session.get(
                        f"{self.services['patient_management']}/patients/{patient_id}"
                    ) as response:
                        if response.status != 200:
                            raise Exception("Failed to get patient data")
                        patient_data = await response.json()
                    
                    # Retry processing
                    result = await self.process_patient(patient_data)
                    results["retried"].append(result)
                    break
                
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        results["failed"].append({
                            "patient_id": patient_id,
                            "error": str(e),
                            "retries": retries
                        })
                    await asyncio.sleep(1)  # Wait before retrying
        
        return results

# Example usage:
# async with ServiceOrchestrator() as orchestrator:
#     # Process single patient
#     result = await orchestrator.process_patient(patient_data)
#     
#     # Process batch of patients
#     results = await orchestrator.batch_process_patients(patients)
#     
#     # Retry failed operations
#     retry_results = await orchestrator.retry_failed_operations(results["failed"])
