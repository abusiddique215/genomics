import subprocess
import time
import sys
import requests
import logging
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceManager:
    def __init__(self):
        self.processes = []
        self.services = [
            {
                'name': 'DynamoDB',
                'command': ['java', '-Djava.library.path=./DynamoDBLocal_lib', '-jar', 'DynamoDBLocal.jar', '-sharedDb'],
                'port': 8000,
                'health_code': 400  # DynamoDB returns 400 for invalid requests
            },
            {
                'name': 'Patient Management',
                'command': [sys.executable, '-m', 'services.patient_management.app'],
                'port': 8080,
                'health_code': 200
            },
            {
                'name': 'Treatment Prediction',
                'command': [sys.executable, '-m', 'services.treatment_prediction.main'],
                'port': 8083,
                'health_code': 200
            },
            {
                'name': 'Data Ingestion',
                'command': [sys.executable, '-m', 'services.data_ingestion.main'],
                'port': 8084,
                'health_code': 200
            }
        ]

    def check_health(self, service: Dict) -> bool:
        """Check if a service is healthy"""
        try:
            response = requests.get(f"http://localhost:{service['port']}/health", timeout=2)
            return response.status_code == service['health_code']
        except:
            return False

    def wait_for_service(self, service: Dict, max_retries: int = 10) -> bool:
        """Wait for a service to become healthy"""
        logger.info(f"Waiting for {service['name']} to start...")
        for i in range(max_retries):
            if self.check_health(service):
                logger.info(f"{service['name']} is healthy")
                return True
            logger.info(f"Waiting... ({i + 1}/{max_retries})")
            time.sleep(2)
        logger.error(f"{service['name']} failed to start")
        return False

    def start_service(self, service: Dict) -> Optional[subprocess.Popen]:
        """Start a single service"""
        try:
            logger.info(f"Starting {service['name']}...")
            process = subprocess.Popen(
                service['command'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if self.wait_for_service(service):
                self.processes.append(process)
                return process
            process.terminate()
            return None
        except Exception as e:
            logger.error(f"Error starting {service['name']}: {str(e)}")
            return None

    def setup_dynamodb(self) -> bool:
        """Set up DynamoDB tables"""
        try:
            logger.info("Setting up DynamoDB tables...")
            result = subprocess.run(
                [sys.executable, 'verify_dynamodb.py'],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.error("DynamoDB setup failed")
                logger.error(result.stderr)
                return False
            logger.info("DynamoDB setup completed")
            return True
        except Exception as e:
            logger.error(f"Error setting up DynamoDB: {str(e)}")
            return False

    def run_tests(self) -> bool:
        """Run system tests"""
        try:
            logger.info("Running system tests...")
            result = subprocess.run(
                [sys.executable, '-m', 'tests.system_test'],
                capture_output=True,
                text=True
            )
            print("\nTest Output:")
            print(result.stdout)
            if result.stderr:
                print("\nTest Errors:")
                print(result.stderr)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error running tests: {str(e)}")
            return False

    def cleanup(self):
        """Clean up all processes"""
        logger.info("Cleaning up...")
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        self.processes = []
        
        # Kill any remaining processes
        try:
            subprocess.run(['pkill', '-f', 'DynamoDBLocal'], capture_output=True)
            subprocess.run(['pkill', '-f', 'services'], capture_output=True)
        except:
            pass
        
        time.sleep(2)
        logger.info("Cleanup complete")

    def run(self):
        """Run the complete system"""
        try:
            # Clean up any existing processes
            self.cleanup()
            
            # Start and verify each service
            for service in self.services:
                if not self.start_service(service):
                    logger.error(f"Failed to start {service['name']}")
                    return False
                logger.info(f"{service['name']} started successfully")
            
            # Set up DynamoDB tables
            if not self.setup_dynamodb():
                return False
            
            # Run tests
            if not self.run_tests():
                logger.error("Tests failed")
                return False
            
            logger.info("\n✅ System is running and all tests passed!")
            logger.info("Press Ctrl+C to stop")
            
            # Keep the system running
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\nShutting down...")
        except Exception as e:
            logger.error(f"Error: {str(e)}")
        finally:
            self.cleanup()

if __name__ == "__main__":
    manager = ServiceManager()
    manager.run()
