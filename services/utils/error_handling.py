from typing import Type, Dict, Any, Optional, Callable
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import traceback
from .logging import get_logger

logger = get_logger('error_handler')

class ServiceError(Exception):
    """Base class for service errors"""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class ValidationServiceError(ServiceError):
    """Validation error"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)

class NotFoundServiceError(ServiceError):
    """Resource not found error"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, details=details)

class AuthenticationError(ServiceError):
    """Authentication error"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)

class AuthorizationError(ServiceError):
    """Authorization error"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, details=details)

async def error_handler(request: Request, call_next: Callable):
    """Middleware to handle errors"""
    try:
        return await call_next(request)
    except Exception as exc:
        return handle_exception(exc, request)

def handle_exception(exc: Exception, request: Request) -> JSONResponse:
    """Handle different types of exceptions"""
    
    # Get request details for logging
    request_details = {
        'method': request.method,
        'url': str(request.url),
        'client_host': request.client.host if request.client else None,
        'headers': dict(request.headers)
    }
    
    if isinstance(exc, ServiceError):
        logger.error(
            f"Service error: {exc.message}",
            extra={
                'status_code': exc.status_code,
                'details': exc.details,
                'request': request_details
            }
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                'error': exc.message,
                'details': exc.details,
                'status_code': exc.status_code
            }
        )
    
    elif isinstance(exc, ValidationError):
        logger.error(
            "Validation error",
            extra={
                'errors': exc.errors(),
                'request': request_details
            }
        )
        return JSONResponse(
            status_code=422,
            content={
                'error': "Validation error",
                'details': exc.errors(),
                'status_code': 422
            }
        )
    
    elif isinstance(exc, HTTPException):
        logger.error(
            f"HTTP error: {exc.detail}",
            extra={
                'status_code': exc.status_code,
                'request': request_details
            }
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                'error': exc.detail,
                'status_code': exc.status_code
            }
        )
    
    else:
        # Unexpected error
        logger.error(
            "Unexpected error",
            exc_info=True,
            extra={'request': request_details}
        )
        return JSONResponse(
            status_code=500,
            content={
                'error': "Internal server error",
                'status_code': 500
            }
        )

def setup_error_handling(app):
    """Set up error handling for FastAPI app"""
    app.middleware('http')(error_handler)

# Example usage:
# from fastapi import FastAPI
# app = FastAPI()
# setup_error_handling(app)
#
# @app.get("/items/{item_id}")
# async def get_item(item_id: str):
#     if not item_exists(item_id):
#         raise NotFoundServiceError(f"Item {item_id} not found")
#     return get_item_data(item_id)
