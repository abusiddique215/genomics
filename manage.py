import subprocess
import time
import sys
import os
import signal
import requests
from typing import List, Optional

def start_dynamodb():
    """Start DynamoDB Local"""
    print("Starting DynamoDB Local...")
    try:
        # Check if DynamoDB is already running
        try:
            subprocess.run(['curl', 'http://localhost:8000'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print("DynamoDB is already running")
            return True
        except subprocess.CalledProcessError:
            pass

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
                subprocess.run(['curl', 'http://localhost:8000'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                print("DynamoDB started successfully!")
                return True
            except subprocess.CalledProcessError:
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
        subprocess.run(['pkill', '-f', pattern], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(1)
    except Exception as e:
        print(f"Warning: Failed to kill {pattern} processes: {str(e)}")

def cleanup():
    """Clean up all running processes"""
    print("\nCleaning up processes...")
    kill_process('DynamoDBLocal')
    kill_process('python -m services')
    time.sleep(2)
    print("Cleanup complete")

def check_service_health(port: int, retries: int = 5) -> bool:
    """Check if a service is healthy"""
    while retries > 0:
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            if response.status_code == 200:
                return True
        except:
            pass
        retries -= 1
        time.sleep(2)
    return False

def run_services():
    """Run all services and tests"""
    try:
        # Start services using start_services.py
        process = subprocess.Popen(
            [sys.executable, 'start_services.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
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
            return False
        
        return True
        
    except Exception as e:
        print(f"Error running services: {str(e)}")
        return False

def main():
    """Main function to manage services"""
    try:
        # Clean up any existing processes
        cleanup()
        
        # Start DynamoDB
        if not start_dynamodb():
            print("Failed to start DynamoDB")
            sys.exit(1)
        
        # Wait for DynamoDB to be fully ready
        time.sleep(5)
        
        # Start services and run tests
        if not run_services():
            print("Service startup failed")
            sys.exit(1)
        
        # Keep the script running
        print("\nServices are running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"\nError: {str(e)}")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
