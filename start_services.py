#!/usr/bin/env python3

import subprocess
import sys
import time
import signal
import os
import logging
import argparse
import requests
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
from config import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceManager:
    """Manage microservices"""
    
    def __init__(self):
        self.services = {
            'dynamodb': {
                'command': 'java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb',
                'port': config.get('ports.dynamodb', 8000),
                'health_endpoint': None,
                'process': None
            },
            'patient_management': {
                'command': 'uvicorn services.patient_management.app:app --host 0.0.0.0 --port 8080 --reload',
                'port': config.get('ports.patient_management', 8080),
                'health_endpoint': '/health',
                'process': None
            },
            'treatment_prediction': {
                'command': 'uvicorn services.treatment_prediction.main:app --host 0.0.0.0 --port 8083 --reload',
                'port': config.get('ports.treatment_prediction', 8083),
                'health_endpoint': '/health',
                'process': None
            },
            'data_ingestion': {
                'command': 'uvicorn services.data_ingestion.main:app --host 0.0.0.0 --port 8084 --reload',
                'port': config.get('ports.data_ingestion', 8084),
                'health_endpoint': '/health',
                'process': None
            }
        }
        self.running = False
    
    def start_service(self, name: str, service: Dict) -> Optional[subprocess.Popen]:
        """Start a single service"""
        try:
            logger.info(f"Starting {name} service...")
            process = subprocess.Popen(
                service['command'].split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            return process
        except Exception as e:
            logger.error(f"Failed to start {name} service: {str(e)}")
            return None
    
    def check_health(self, name: str, service: Dict) -> bool:
        """Check service health"""
        if not service['health_endpoint']:
            return True
        
        url = f"http://localhost:{service['port']}{service['health_endpoint']}"
        try:
            response = requests.get(url)
            return response.status_code == 200
        except:
            return False
    
    def wait_for_service(self, name: str, service: Dict, timeout: int = 30) -> bool:
        """Wait for service to be healthy"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.check_health(name, service):
                logger.info(f"{name} service is healthy")
                return True
            time.sleep(1)
        
        logger.error(f"{name} service failed to become healthy")
        return False
    
    def start_all(self, dev_mode: bool = False):
        """Start all services"""
        if self.running:
            logger.warning("Services are already running")
            return
        
        self.running = True
        
        # Start DynamoDB first
        dynamodb = self.services['dynamodb']
        dynamodb['process'] = self.start_service('dynamodb', dynamodb)
        time.sleep(2)  # Wait for DynamoDB to start
        
        # Start other services
        for name, service in self.services.items():
            if name != 'dynamodb':
                service['process'] = self.start_service(name, service)
        
        # Wait for all services to be healthy
        with ThreadPoolExecutor() as executor:
            results = executor.map(
                lambda x: self.wait_for_service(x[0], x[1]),
                [(n, s) for n, s in self.services.items() if n != 'dynamodb']
            )
        
        if not all(results):
            logger.error("Not all services started successfully")
            self.stop_all()
            sys.exit(1)
        
        logger.info("All services started successfully")
    
    def stop_all(self):
        """Stop all services"""
        if not self.running:
            logger.warning("No services are running")
            return
        
        for name, service in self.services.items():
            if service['process']:
                logger.info(f"Stopping {name} service...")
                service['process'].terminate()
                service['process'].wait()
                service['process'] = None
        
        self.running = False
        logger.info("All services stopped")
    
    def check_all(self) -> bool:
        """Check health of all services"""
        results = []
        for name, service in self.services.items():
            if name != 'dynamodb':  # Skip DynamoDB health check
                healthy = self.check_health(name, service)
                results.append(healthy)
                status = "healthy" if healthy else "unhealthy"
                logger.info(f"{name} service is {status}")
        
        return all(results)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal")
    manager.stop_all()
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Start microservices")
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Start in development mode with auto-reload"
    )
    args = parser.parse_args()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        manager.start_all(dev_mode=args.dev)
        
        # Keep the script running
        while True:
            time.sleep(1)
            if not manager.check_all():
                logger.error("Service health check failed")
                manager.stop_all()
                sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        manager.stop_all()
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        manager.stop_all()
        sys.exit(1)

if __name__ == "__main__":
    manager = ServiceManager()
    main()
