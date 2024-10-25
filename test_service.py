import requests
import time
import sys

def test_service():
    """Test if the service is running and responding"""
    print("Testing service...")
    
    # Wait for service to start
    time.sleep(2)
    
    try:
        # Test root endpoint
        response = requests.get("http://localhost:8000/")
        print(f"\nRoot endpoint response ({response.status_code}):")
        print(response.json())
        
        # Test health endpoint
        response = requests.get("http://localhost:8000/health")
        print(f"\nHealth endpoint response ({response.status_code}):")
        print(response.json())
        
    except requests.exceptions.ConnectionError:
        print("Failed to connect to service")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    if test_service():
        print("\nService is running and responding!")
        sys.exit(0)
    else:
        print("\nService test failed!")
        sys.exit(1)
