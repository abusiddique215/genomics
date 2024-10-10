import subprocess
import time
import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

services = [
    ("dashboard", "python services/dashboard/main.py"),
    ("patient_management", "python services/patient_management/main.py"),
    ("rag_pipeline", "python services/rag_pipeline/main.py"),
    ("model_training", "python services/model_training/main.py"),
    ("powerbi_integration", "python services/powerbi_integration/main.py")
]

def start_service(name, command):
    print(f"Starting {name} service...")
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{project_root}:{env.get('PYTHONPATH', '')}"
        process = subprocess.Popen(command, shell=True, env=env)
        print(f"{name} service started with PID {process.pid}")
        return process
    except Exception as e:
        print(f"Error starting {name} service: {str(e)}")
        return None

def main():
    processes = []
    for name, command in services:
        process = start_service(name, command)
        if process:
            processes.append((name, process))
        time.sleep(2)  # Wait a bit between starting services

    print("All services started. Press Ctrl+C to stop all services.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping all services...")
        for name, process in processes:
            print(f"Stopping {name} service...")
            process.terminate()
            process.wait()
        print("All services stopped.")

if __name__ == "__main__":
    main()