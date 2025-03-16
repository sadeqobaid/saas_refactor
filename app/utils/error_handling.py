"""
Error handling utilities for the SaaS Platform.

This module provides centralized error handling with request ID correlation.
"""

import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError

from app.utils.logging import get_logger

# Set up logger
logger = get_logger(__name__)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation exceptions with request ID correlation.
    
    Args:
        request: FastAPI request object
        exc: Validation exception
        
    Returns:
        JSONResponse: Error response with details and request ID
    """
    request_id = getattr(request.state, "request_id", "no-request-id")
    
    # Log the error with request ID
    logger.error(
        f"Validation error: {exc}",
        extra={"request_id": request_id}
    )
    
    # Return structured error response
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "request_id": request_id,
            "message": "Validation error"
        }
    )

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Handle SQLAlchemy exceptions with request ID correlation.
    
    Args:
        request: FastAPI request object
        exc: SQLAlchemy exception
        
    Returns:
        JSONResponse: Error response with request ID
    """
    request_id = getattr(request.state, "request_id", "no-request-id")
    
    # Log the error with request ID and traceback
    logger.error(
        f"Database error: {str(exc)}",
        extra={
            "request_id": request_id,
            "traceback": traceback.format_exc()
        }
    )
    
    # Return structured error response
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Database error occurred",
            "request_id": request_id,
            "message": "Internal server error"
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle general exceptions with request ID correlation.
    
    Args:
        request: FastAPI request object
        exc: Exception
        
    Returns:
        JSONResponse: Error response with request ID
    """
    request_id = getattr(request.state, "request_id", "no-request-id")
    
    # Log the error with request ID and traceback
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "request_id": request_id,
            "traceback": traceback.format_exc()
        }
    )
    
    # Return structured error response
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "request_id": request_id,
            "message": "Internal server error"
        }
    )

def setup_error_handlers(app):
    """
    Set up error handlers for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
