import os
import sys
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional
import json
from functools import wraps
import time
import traceback
from contextlib import contextmanager  # Add this import
from config import config

class CustomJsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def __init__(self, **kwargs):
        super().__init__()
        self.kwargs = kwargs

    def format(self, record):
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
            
        # Add custom fields
        log_data.update(self.kwargs)
        
        return json.dumps(log_data)

def setup_logging(
    service_name: str,
    log_level: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """Set up logging configuration for a service"""
    
    # Get configuration
    log_config = config.get('logging', {})
    level = log_level or log_config.get('level', 'INFO')
    log_format = log_config.get('format')
    
    # Create logger
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomJsonFormatter(service=service_name))
    logger.addHandler(console_handler)
    
    # Create file handler if log file specified
    if log_file or log_config.get('file'):
        file_path = Path(log_file or log_config['file'])
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=parse_size(log_config.get('max_size', '10MB')),
            backupCount=log_config.get('backup_count', 5)
        )
        file_handler.setFormatter(CustomJsonFormatter(service=service_name))
        logger.addHandler(file_handler)
    
    return logger

def parse_size(size_str: str) -> int:
    """Parse size string (e.g., '10MB') to bytes"""
    units = {'B': 1, 'KB': 1024, 'MB': 1024*1024, 'GB': 1024*1024*1024}
    number = float(''.join(filter(str.isdigit, size_str)))
    unit = ''.join(filter(str.isalpha, size_str)).upper()
    return int(number * units[unit])

def log_execution_time(logger: logging.Logger):
    """Decorator to log function execution time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    f"Function {func.__name__} executed in {execution_time:.2f} seconds",
                    extra={'execution_time': execution_time}
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Function {func.__name__} failed after {execution_time:.2f} seconds",
                    exc_info=True,
                    extra={'execution_time': execution_time}
                )
                raise
        return wrapper
    return decorator

class ServiceLogger:
    """Logger class for services with context tracking"""
    
    def __init__(self, service_name: str):
        self.logger = setup_logging(service_name)
        self.context = {}
    
    def add_context(self, **kwargs):
        """Add context to all subsequent log messages"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear the current context"""
        self.context.clear()
    
    def _log(self, level: str, message: str, **kwargs):
        """Internal logging method"""
        extra_data = {**self.context, **kwargs}
        if 'extra_data' in kwargs:
            extra_data.update(kwargs['extra_data'])
        
        getattr(self.logger, level)(
            message,
            extra={'extra_data': extra_data},
            exc_info=kwargs.get('exc_info', None)
        )
    
    def debug(self, message: str, **kwargs):
        self._log('debug', message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log('info', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log('warning', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log('error', message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log('critical', message, **kwargs)
    
    @contextmanager
    def context_scope(self, **kwargs):
        """Context manager for temporary context"""
        original_context = self.context.copy()
        self.add_context(**kwargs)
        try:
            yield
        finally:
            self.context = original_context

def get_logger(service_name: str) -> ServiceLogger:
    """Get a configured logger for a service"""
    return ServiceLogger(service_name)

# Example usage:
# logger = get_logger('patient_management')
# logger.add_context(request_id='123')
# 
# @log_execution_time(logger)
# def process_patient(patient_id: str):
#     with logger.context_scope(patient_id=patient_id):
#         logger.info("Processing patient")
#         # ... processing logic ...
