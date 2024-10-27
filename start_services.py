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

def check_port(port: int) -> bool:
    """Check if a port is in use"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def wait_for_port(port: int, timeout: int = 20) -> bool:
    """Wait for a port to become available"""
    retries = timeout
    while retries > 0:
        if not check_port(port):
            return True
        print(f"Waiting for port {port} to become available... ({retries} retries left)")
        time.sleep(1)
        retries -= 1
    return False

def check_service_health(port: int) -> bool:
    """Check if a service is healthy"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_service(service: Dict) -> Optional[subprocess.Popen]:
    """Start a single service"""
    try:
        print(f"\nStarting {service['name']} service...")
        
        # Wait for port to become available
        if not wait_for_port(service['port']):
            print(f"Port {service['port']} is still in use")
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
            if check_service_health(service['port']):
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

def run_tests() -> bool:
    """Run system tests"""
    print("\nRunning system tests...")
    try:
        # Wait for all services to be healthy
        print("Waiting for all services to be healthy...")
        time.sleep(5)  # Give services time to fully initialize
        
        ports = [8080, 8083, 8084]  # Patient Management, Treatment Prediction, Data Ingestion
        for port in ports:
            retries = 5
            while retries > 0:
                if check_service_health(port):
                    break
                print(f"Waiting for service on port {port} to be healthy... ({retries} retries left)")
                time.sleep(2)
                retries -= 1
            if retries == 0:
                print(f"Service on port {port} is not healthy")
                return False
        
        # Run the tests
        result = subprocess.run(
            [sys.executable, '-m', 'tests.system_test'],
            capture_output=True,
            text=True
        )
        
        # Print test output
        if result.stdout:
            print("\nTest output:")
            print(result.stdout)
        if result.stderr:
            print("\nTest errors:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running tests: {str(e)}")
        return False

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
        
        # Run the tests
        if not run_tests():
            print("\n❌ Tests failed!")
            sys.exit(1)
        
        print("\n✅ All tests passed!")
        
        # Keep services running
        print("\nServices are running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down services...")
    except Exception as e:
        print(f"\nError: {str(e)}")
    finally:
        for process in processes:
            process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    start_services()
