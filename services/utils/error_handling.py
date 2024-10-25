from fastapi import HTTPException
from typing import Dict, Any, Optional
from .logging import get_logger

logger = get_logger()

class GenomicsError(Exception):
    """Base exception class for genomics application"""
    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class DataValidationError(GenomicsError):
    """Raised when data validation fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)

class ModelPredictionError(GenomicsError):
    """Raised when model prediction fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "PREDICTION_ERROR", details)

class DatabaseError(GenomicsError):
    """Raised when database operations fail"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATABASE_ERROR", details)

def handle_error(error: Exception, service: str) -> HTTPException:
    """Convert application errors to HTTP exceptions and log them"""
    if isinstance(error, GenomicsError):
        status_code = {
            "VALIDATION_ERROR": 400,
            "PREDICTION_ERROR": 500,
            "DATABASE_ERROR": 503
        }.get(error.error_code, 500)
        
        # Log the error
        logger.log_error(service, error, error.details)
        
        return HTTPException(
            status_code=status_code,
            detail={
                "error_code": error.error_code,
                "message": error.message,
                "details": error.details
            }
        )
    else:
        # Log unexpected errors
        logger.log_error(service, error)
        
        return HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"error_type": type(error).__name__}
            }
        )

def validate_patient_data(data: Dict[str, Any]):
    """Validate patient data"""
    required_fields = ['id', 'name', 'age']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        raise DataValidationError(
            "Missing required fields",
            {"missing_fields": missing_fields}
        )
    
    if not isinstance(data.get('age'), (int, float)) or data['age'] < 0 or data['age'] > 150:
        raise DataValidationError(
            "Invalid age value",
            {"age": data.get('age')}
        )

def validate_genomic_data(data: Dict[str, Any]):
    """Validate genomic data"""
    if not isinstance(data, dict):
        raise DataValidationError(
            "Genomic data must be a dictionary",
            {"data_type": type(data).__name__}
        )
    
    # Add more specific validation as needed
    pass

def validate_medical_history(data: Dict[str, Any]):
    """Validate medical history data"""
    if not isinstance(data, dict):
        raise DataValidationError(
            "Medical history must be a dictionary",
            {"data_type": type(data).__name__}
        )
    
    # Add more specific validation as needed
    pass
