#!/usr/bin/env python3

import requests
import subprocess
import time
import logging
import sys
import os
import json
from typing import Dict, List, Any, Optional
import psutil
from config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceVerifier:
    """Verify all services are running and healthy"""
    
    def __init__(self):
        self.services = {
            'patient_management': {
                'url': config.get('services.patient_management'),
                'port': config.get('ports.patient_management', 8080),
                'health_endpoint': '/health'
            },
            'treatment_prediction': {
                'url': config.get('services.treatment_prediction'),
                'port': config.get('ports.treatment_prediction', 8083),
                'health_endpoint': '/health'
            },
            'data_ingestion': {
                'url': config.get('services.data_ingestion'),
                'port': config.get('ports.data_ingestion', 8084),
                'health_endpoint': '/health'
            }
        }
        self.dynamodb_port = config.get('ports.dynamodb', 8000)
    
    def check_port_in_use(self, port: int) -> bool:
        """Check if a port is in use"""
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                return True
        return False
    
    def verify_dynamodb(self) -> bool:
        """Verify DynamoDB is running"""
        if not self.check_port_in_use(self.dynamodb_port):
            logger.error("DynamoDB is not running")
            return False
        
        try:
            # Try to list tables
            import boto3
            dynamodb = boto3.client(
                'dynamodb',
                endpoint_url=f'http://localhost:{self.dynamodb_port}',
                region_name='us-west-2'
            )
            dynamodb.list_tables()
            logger.info("DynamoDB is running and responsive")
            return True
        except Exception as e:
            logger.error(f"DynamoDB verification failed: {str(e)}")
            return False
    
    def verify_service(self, name: str, service: Dict[str, Any]) -> bool:
        """Verify a single service"""
        # Check if port is in use
        if not self.check_port_in_use(service['port']):
            logger.error(f"{name} service is not running")
            return False
        
        # Check health endpoint
        try:
            url = f"{service['url']}{service['health_endpoint']}"
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                logger.error(f"{name} service health check failed")
                return False
            
            logger.info(f"{name} service is healthy")
            return True
        except Exception as e:
            logger.error(f"{name} service verification failed: {str(e)}")
            return False
    
    def verify_service_integration(self) -> bool:
        """Verify service integration"""
        try:
            # Generate test patient
            test_patient = {
                "id": "TEST_INTEGRATION",
                "name": "Test Patient",
                "age": 45,
                "genomic_data": {
                    "gene_variants": {"BRCA1": "variant1"},
                    "mutation_scores": {"BRCA1": "0.8"}
                },
                "medical_history": {
                    "conditions": ["condition1"],
                    "treatments": [],
                    "allergies": []
                }
            }
            
            # Test data ingestion
            response = requests.post(
                f"{self.services['data_ingestion']['url']}/ingest/patient",
                json=test_patient
            )
            if response.status_code != 200:
                logger.error("Data ingestion failed")
                return False
            
            # Test patient retrieval
            response = requests.get(
                f"{self.services['patient_management']['url']}/patients/{test_patient['id']}"
            )
            if response.status_code != 200:
                logger.error("Patient retrieval failed")
                return False
            
            # Test treatment prediction
            response = requests.post(
                f"{self.services['treatment_prediction']['url']}/predict",
                json={
                    "genomic_data": test_patient["genomic_data"],
                    "medical_history": test_patient["medical_history"]
                }
            )
            if response.status_code != 200:
                logger.error("Treatment prediction failed")
                return False
            
            logger.info("Service integration test passed")
            return True
            
        except Exception as e:
            logger.error(f"Integration test failed: {str(e)}")
            return False
    
    def verify_metrics(self) -> bool:
        """Verify metrics collection"""
        try:
            metrics_port = config.get('monitoring.metrics_port', 9090)
            response = requests.get(f"http://localhost:{metrics_port}/metrics")
            if response.status_code != 200:
                logger.error("Metrics endpoint is not accessible")
                return False
            
            logger.info("Metrics collection is working")
            return True
        except Exception as e:
            logger.error(f"Metrics verification failed: {str(e)}")
            return False
    
    def run_all_verifications(self) -> bool:
        """Run all verifications"""
        verifications = [
            (self.verify_dynamodb, "DynamoDB"),
            *[(lambda s=s, d=d: self.verify_service(s, d), s)
              for s, d in self.services.items()],
            (self.verify_service_integration, "Service Integration"),
            (self.verify_metrics, "Metrics Collection")
        ]
        
        all_passed = True
        for verify_func, name in verifications:
            logger.info(f"Verifying {name}...")
            if not verify_func():
                logger.error(f"{name} verification failed")
                all_passed = False
            else:
                logger.info(f"{name} verification passed")
        
        return all_passed

def main():
    """Main function"""
    verifier = ServiceVerifier()
    if not verifier.run_all_verifications():
        logger.error("Service verification failed")
        sys.exit(1)
    logger.info("All services verified successfully")

if __name__ == '__main__':
    main()
