import requests
import sys
import time

def check_service(name: str, port: int) -> bool:
    """Check if a service is running and healthy"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=2)
        if response.status_code == 200:
            print(f"✅ {name} is running and healthy")
            return True
        print(f"❌ {name} returned status code {response.status_code}")
        return False
    except requests.exceptions.RequestException:
        print(f"❌ {name} is not responding")
        return False

def main():
    """Check all services"""
    services = [
        ("DynamoDB", 8000),
        ("Patient Management", 8080),
        ("Treatment Prediction", 8083),
        ("Data Ingestion", 8084)
    ]
    
    all_healthy = True
    for name, port in services:
        if not check_service(name, port):
            all_healthy = False
    
    if all_healthy:
        print("\n✅ All services are running!")
        sys.exit(0)
    else:
        print("\n❌ Some services are not running!")
        sys.exit(1)

if __name__ == "__main__":
    main()
