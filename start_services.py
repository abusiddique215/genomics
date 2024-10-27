import subprocess
import time
import sys
import os
import signal
import requests
from typing import List, Dict, Optional

def verify_dynamodb():
    """Run DynamoDB verification"""
    result = subprocess.run([sys.executable, 'verify_dynamodb.py'])
    return result.returncode == 0

def kill_existing_processes():
    """Kill any existing Python processes"""
    try:
        # Kill any existing Python processes
        subprocess.run(['pkill', '-f', 'python'])
        time.sleep(2)  # Wait for processes to be killed
    except Exception as e:
        print(f"Warning: Failed to kill existing processes: {str(e)}")

def check_port(port: int) -> bool:
    """Check if a port is in use"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=1)
        return response.status_code == 200
    except:
        return False

def start_service(service: Dict) -> Optional[subprocess.Popen]:
    """Start a single service"""
    try:
        print(f"\nStarting {service['name']} service...")
        
        # Check if service is already running
        if check_port(service['port']):
            print(f"{service['name']} is already running on port {service['port']}")
            return None
        
        # Start the service
        process = subprocess.Popen(
            service['command'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Wait for service to start
        retries = 10
        while retries > 0:
            if check_port(service['port']):
                print(f"{service['name']} service is healthy")
                return process
            print(f"Waiting for {service['name']} to start... ({retries} retries left)")
            time.sleep(2)
            retries -= 1
        
        print(f"Warning: Could not verify {service['name']} health")
        return process
        
    except Exception as e:
        print(f"Error starting {service['name']}: {str(e)}")
        return None

def start_services():
    """Start all required services"""
    # First verify DynamoDB is running and tables are created
    print("Verifying DynamoDB setup...")
    if not verify_dynamodb():
        print("Error: DynamoDB verification failed")
        sys.exit(1)
    
    # Define services
    services = [
        {
            'name': 'Patient Management',
            'command': [sys.executable, '-m', 'services.patient_management.app'],
            'port': 8080
        },
        {
            'name': 'Treatment Prediction',
            'command': [sys.executable, '-m', 'services.treatment_prediction.main'],
            'port': 8083
        },
        {
            'name': 'Data Ingestion',
            'command': [sys.executable, '-m', 'services.data_ingestion.main'],
            'port': 8084
        }
    ]

    processes = []
    
    try:
        print("Starting services...")
        
        # Kill any existing processes
        kill_existing_processes()
        
        # Start each service
        for service in services:
            process = start_service(service)
            if process:
                processes.append(process)
                print(f"{service['name']} service started on port {service['port']}")
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
