import subprocess
import time
import sys
import os
import signal
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
        subprocess.run(['pkill', '-f', pattern])
        time.sleep(1)
    except Exception as e:
        print(f"Warning: Failed to kill {pattern} processes: {str(e)}")

def cleanup():
    """Clean up all running processes"""
    print("\nCleaning up processes...")
    kill_process('DynamoDBLocal')
    kill_process('python -m services')
    time.sleep(2)

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
        
        # Start our services
        print("\nStarting application services...")
        subprocess.run([sys.executable, 'start_services.py'])
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"\nError: {str(e)}")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
