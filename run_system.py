import subprocess
import time
import sys
import requests
import logging
import threading
from typing import List, Dict, Optional
from queue import Queue, Empty

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def log_stream(stream, prefix: str, queue: Queue):
    """Log output from a stream"""
    for line in iter(stream.readline, b''):
        line = line.decode('utf-8').rstrip()
        queue.put(f"{prefix}: {line}")

class ServiceManager:
    def __init__(self):
        self.processes = []
        self.output_queue = Queue()
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
            if service['name'] == 'DynamoDB':
                response = requests.post('http://localhost:8000', timeout=2)
                return response.status_code == 400
            else:
                response = requests.get(f"http://localhost:{service['port']}/health", timeout=2)
                return response.status_code == service['health_code']
        except:
            return False

    def wait_for_service(self, service: Dict, max_retries: int = 30) -> bool:
        """Wait for a service to become healthy"""
        logger.info(f"Waiting for {service['name']} to start...")
        for i in range(max_retries):
            if self.check_health(service):
                logger.info(f"{service['name']} is healthy")
                return True
            logger.info(f"Waiting... ({i + 1}/{max_retries})")
            time.sleep(2)
            
            # Print any queued output
            try:
                while True:
                    print(self.output_queue.get_nowait())
            except Empty:
                pass
                
        logger.error(f"{service['name']} failed to start")
        return False

    def start_service(self, service: Dict) -> Optional[subprocess.Popen]:
        """Start a single service"""
        try:
            logger.info(f"Starting {service['name']}...")
            
            # Start the process with pipe for output
            process = subprocess.Popen(
                service['command'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True
            )
            
            # Start threads to handle output
            threading.Thread(
                target=log_stream,
                args=(process.stdout, f"{service['name']} OUT", self.output_queue),
                daemon=True
            ).start()
            threading.Thread(
                target=log_stream,
                args=(process.stderr, f"{service['name']} ERR", self.output_queue),
                daemon=True
            ).start()
            
            if self.wait_for_service(service):
                self.processes.append(process)
                return process
                
            # If service failed to start, print its output
            logger.error(f"{service['name']} output:")
            try:
                while True:
                    print(self.output_queue.get_nowait())
            except Empty:
                pass
                
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
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            if result.returncode != 0:
                logger.error("DynamoDB setup failed")
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
            
            # Keep the system running and print output
            while True:
                try:
                    print(self.output_queue.get(timeout=1))
                except Empty:
                    pass
                
        except KeyboardInterrupt:
            logger.info("\nShutting down...")
        except Exception as e:
            logger.error(f"Error: {str(e)}")
        finally:
            self.cleanup()

if __name__ == "__main__":
    manager = ServiceManager()
    manager.run()
