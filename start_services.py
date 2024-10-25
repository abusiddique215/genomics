import subprocess
import time
import sys
import os
import signal
from typing import List, Dict
import requests

def start_service(service: Dict):
    """Start a single service"""
    try:
        print(f"\nStarting {service['name']} service...")
        process = subprocess.Popen(
            service['command'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Wait for service to start
        time.sleep(5)
        return process
        
    except Exception as e:
        print(f"Error starting {service['name']}: {str(e)}")
        return None

def check_service_health(port: int) -> bool:
    """Check if a service is healthy by attempting to connect"""
    try:
        response = requests.get(f"http://localhost:{port}/health")
        return response.status_code == 200
    except:
        return False

def start_services():
    """Start all required services"""
    # Define services
    services = [
        {
            'name': 'Patient Management',
            'command': ['python', '-m', 'services.patient_management.app'],
            'port': 8501
        },
        {
            'name': 'Treatment Prediction',
            'command': ['python', '-m', 'services.treatment_prediction.main'],
            'port': 8083
        },
        {
            'name': 'Data Ingestion',
            'command': ['python', '-m', 'services.data_ingestion.main'],
            'port': 8084
        }
    ]

    processes = []
    
    try:
        print("Starting services...")
        
        # Start each service
        for service in services:
            process = start_service(service)
            if process:
                processes.append(process)
                print(f"{service['name']} service started on port {service['port']}")
                
                # Check service health
                retries = 3
                while retries > 0:
                    if check_service_health(service['port']):
                        print(f"{service['name']} service is healthy")
                        break
                    retries -= 1
                    time.sleep(2)
                
                if retries == 0:
                    print(f"Warning: Could not verify {service['name']} health")
            else:
                print(f"Failed to start {service['name']}")
                # Cleanup already started processes
                for p in processes:
                    p.terminate()
                sys.exit(1)
        
        print("\nAll services started!")
        
        # Run the system tests
        print("\nRunning system tests...")
        subprocess.run([sys.executable, '-m', 'tests.system_test'])
        
    except KeyboardInterrupt:
        print("\nShutting down services...")
        for process in processes:
            process.terminate()
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {str(e)}")
        for process in processes:
            process.terminate()
        sys.exit(1)

if __name__ == "__main__":
    start_services()
