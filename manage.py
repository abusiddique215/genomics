import subprocess
import time
import sys
import os
import signal
import requests
from typing import List, Optional

def check_port(port: int) -> bool:
    """Check if a port is in use"""
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
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

def start_dynamodb():
    """Start DynamoDB Local"""
    print("Starting DynamoDB Local...")
    try:
        # Kill any existing DynamoDB process
        kill_process('DynamoDBLocal')
        
        # Wait for port 8000 to become available
        if not wait_for_port(8000):
            print("Failed to free up port 8000")
            return False
        
        # Start DynamoDB in the background
        process = subprocess.Popen(
            ['java', '-Djava.library.path=./DynamoDBLocal_lib', '-jar', 'DynamoDBLocal.jar', '-sharedDb'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for DynamoDB to start
        retries = 10
        while retries > 0:
            try:
                response = requests.get('http://localhost:8000')
                if response.status_code == 400:  # DynamoDB returns 400 for invalid requests
                    print("DynamoDB started successfully!")
                    return True
            except requests.exceptions.ConnectionError:
                print(f"Waiting for DynamoDB to start... ({retries} retries left)")
                time.sleep(2)
                retries -= 1
        
        print("Failed to start DynamoDB")
        return False
        
    except Exception as e:
        print(f"Error starting DynamoDB: {str(e)}")
        return False

def kill_process(pattern: str):
    """Kill processes matching the pattern"""
    try:
        # Try pkill first
        subprocess.run(['pkill', '-f', pattern], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # If process is still running, try SIGKILL
        time.sleep(1)
        if pattern == 'DynamoDBLocal' and check_port(8000):
            subprocess.run(['pkill', '-9', '-f', pattern], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(1)
    except Exception as e:
        print(f"Warning: Failed to kill {pattern} processes: {str(e)}")

def cleanup():
    """Clean up all running processes"""
    print("\nCleaning up processes...")
    
    # Kill Python services
    kill_process('services.patient_management.app')
    kill_process('services.treatment_prediction.main')
    kill_process('services.data_ingestion.main')
    
    # Kill DynamoDB
    kill_process('DynamoDBLocal')
    
    # Wait for all ports to be freed
    ports = [8000, 8080, 8083, 8084]
    for port in ports:
        wait_for_port(port)
    
    print("Cleanup complete")

def verify_service_ports():
    """Verify all required ports are available"""
    ports = {
        8000: "DynamoDB",
        8080: "Patient Management",
        8083: "Treatment Prediction",
        8084: "Data Ingestion"
    }
    
    for port, service in ports.items():
        if check_port(port):
            print(f"Port {port} is in use (used by {service})")
            return False
    return True

def main():
    """Main function to manage services"""
    try:
        # Clean up any existing processes
        cleanup()
        
        # Verify ports are available
        if not verify_service_ports():
            print("Some ports are still in use. Please check running processes.")
            sys.exit(1)
        
        # Start DynamoDB
        if not start_dynamodb():
            print("Failed to start DynamoDB")
            sys.exit(1)
        
        # Wait for DynamoDB to be fully ready
        time.sleep(5)
        
        # Start our services
        print("\nStarting application services...")
        process = subprocess.Popen(
            [sys.executable, 'start_services.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Print output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        # Check if process failed
        if process.returncode != 0:
            print("Failed to start services")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"\nError: {str(e)}")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
