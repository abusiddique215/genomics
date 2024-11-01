#!/usr/bin/env python3

import argparse
import asyncio
import logging
import sys
import signal
from typing import Dict, Any, Optional
from datetime import datetime
from config import config
from services.utils.logging import get_logger
from services.utils.monitoring import ServiceMonitor
from services.utils.orchestration import ServiceOrchestrator

# Set up logging
logger = get_logger('system')

class SystemManager:
    """Manage the entire genomics system"""
    
    def __init__(self):
        self.monitor = ServiceMonitor('system')
        self.orchestrator: Optional[ServiceOrchestrator] = None
        self.running = False
    
    async def start(self, dev_mode: bool = False):
        """Start the system"""
        if self.running:
            logger.warning("System is already running")
            return
        
        try:
            # Start monitoring
            self.monitor.start_resource_monitoring()
            
            # Initialize orchestrator
            self.orchestrator = ServiceOrchestrator()
            async with self.orchestrator as orch:
                # Verify services
                service_status = await orch.check_all_services()
                if not all(service_status.values()):
                    failed_services = [
                        name for name, status in service_status.items()
                        if not status
                    ]
                    raise Exception(f"Services not healthy: {failed_services}")
                
                self.running = True
                logger.info("System started successfully")
                
                # Keep running until stopped
                while self.running:
                    # Periodic health check
                    service_status = await orch.check_all_services()
                    if not all(service_status.values()):
                        logger.error("Service health check failed")
                        await self.stop()
                        break
                    
                    await asyncio.sleep(30)
        
        except Exception as e:
            logger.error(f"Failed to start system: {str(e)}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the system"""
        if not self.running:
            return
        
        logger.info("Stopping system...")
        self.running = False
        
        # Additional cleanup if needed
        logger.info("System stopped")
    
    async def process_batch(self, input_file: str) -> Dict[str, Any]:
        """Process a batch of patients"""
        if not self.orchestrator:
            raise Exception("System not started")
        
        try:
            # Load patients from file
            with open(input_file, 'r') as f:
                import json
                patients = json.load(f)
            
            # Process batch
            results = await self.orchestrator.batch_process_patients(patients)
            
            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"data/results_{timestamp}.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            return {
                "processed": len(patients),
                "successful": results["successful_count"],
                "failed": results["failed_count"],
                "output_file": output_file
            }
        
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            raise

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run genomics system')
    parser.add_argument(
        '--dev',
        action='store_true',
        help='Run in development mode'
    )
    parser.add_argument(
        '--batch',
        type=str,
        help='Process batch from input file'
    )
    
    args = parser.parse_args()
    manager = SystemManager()
    
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(manager.stop())
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await manager.start(dev_mode=args.dev)
        
        if args.batch:
            results = await manager.process_batch(args.batch)
            logger.info(f"Batch processing results: {results}")
        
        # Keep running until stopped
        while manager.running:
            await asyncio.sleep(1)
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await manager.stop()
        sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await manager.stop()

if __name__ == "__main__":
    asyncio.run(main())
