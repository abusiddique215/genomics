from fastapi import HTTPException
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class GenomicsError(Exception):
    """Base exception class for genomics application"""
    def __init__(self, message: str, error_code: str, status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)

class ValidationError(GenomicsError):
    """Raised when input validation fails"""
    def __init__(self, message: str, field: str):
        super().__init__(
            message=f"Validation error for field '{field}': {message}",
            error_code="VALIDATION_ERROR",
            status_code=400
        )

class DatabaseError(GenomicsError):
    """Raised when database operations fail"""
    def __init__(self, message: str):
        super().__init__(
            message=f"Database error: {message}",
            error_code="DATABASE_ERROR",
            status_code=500
        )

def handle_error(error: Exception) -> Dict[str, Any]:
    """Convert exceptions to FastAPI HTTP responses"""
    if isinstance(error, GenomicsError):
        logger.error(f"{error.error_code}: {error.message}")
        raise HTTPException(
            status_code=error.status_code,
            detail={
                "error_code": error.error_code,
                "message": error.message
            }
        )
    else:
        logger.error(f"Unexpected error: {str(error)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred"
            }
        )

def validate_patient_data(data: Dict[str, Any]) -> None:
    """Validate patient data fields"""
    # Validate ID
    if not data.get('id'):
        raise ValidationError("ID is required", "id")
    if not isinstance(data['id'], str):
        raise ValidationError("ID must be a string", "id")
    
    # Validate Name
    if not data.get('name'):
        raise ValidationError("Name is required", "name")
    if not isinstance(data['name'], str):
        raise ValidationError("Name must be a string", "name")
    if len(data['name']) < 2:
        raise ValidationError("Name must be at least 2 characters long", "name")
    
    # Validate Age
    if not isinstance(data.get('age'), int):
        raise ValidationError("Age must be an integer", "age")
    if data['age'] < 0 or data['age'] > 150:
        raise ValidationError("Age must be between 0 and 150", "age")
    
    # Validate Genomic Data
    if not isinstance(data.get('genomic_data'), dict):
        raise ValidationError("Genomic data must be a dictionary", "genomic_data")
    
    # Validate Medical History
    if not isinstance(data.get('medical_history'), dict):
        raise ValidationError("Medical history must be a dictionary", "medical_history")

def format_error_response(error: Exception) -> Dict[str, Any]:
    """Format error response for the frontend"""
    if isinstance(error, GenomicsError):
        return {
            "error_code": error.error_code,
            "message": error.message,
            "status": error.status_code
        }
    return {
        "error_code": "INTERNAL_SERVER_ERROR",
        "message": str(error),
        "status": 500
    }
