import logging
from datetime import datetime
import os
from typing import Dict, Any
import json
import traceback

class GenomicsLogger:
    def __init__(self):
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Configure logging
        self.logger = logging.getLogger('genomics')
        self.logger.setLevel(logging.INFO)
        
        # File handler for all logs
        fh = logging.FileHandler(f'logs/genomics_{datetime.now():%Y%m%d}.log')
        fh.setLevel(logging.INFO)
        
        # Error file handler
        error_fh = logging.FileHandler(f'logs/errors_{datetime.now():%Y%m%d}.log')
        error_fh.setLevel(logging.ERROR)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        error_fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(fh)
        self.logger.addHandler(error_fh)
        self.logger.addHandler(ch)
    
    def log_event(self, service: str, event_type: str, data: Dict[str, Any]):
        """Log an event with structured data"""
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'service': service,
                'event_type': event_type,
                'data': data
            }
            self.logger.info(json.dumps(log_entry))
        except Exception as e:
            self.logger.error(f"Error logging event: {str(e)}")
    
    def log_error(self, service: str, error: Exception, context: Dict[str, Any] = None):
        """Log an error with stack trace and context"""
        try:
            error_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'service': service,
                'error_type': type(error).__name__,
                'error_message': str(error),
                'stack_trace': traceback.format_exc(),
                'context': context or {}
            }
            self.logger.error(json.dumps(error_entry))
        except Exception as e:
            self.logger.error(f"Error logging error: {str(e)}")

# Initialize global logger instance
genomics_logger = GenomicsLogger()

def get_logger():
    """Get the global logger instance"""
    return genomics_logger
