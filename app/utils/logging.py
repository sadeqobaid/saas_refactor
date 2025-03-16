"""
Logging configuration module for the SaaS Platform.

This module sets up structured logging with request ID correlation.
"""

import logging
import json
from datetime import datetime
from typing import Optional
from fastapi import Request

class RequestIdFilter(logging.Filter):
    """
    Logging filter that adds request_id to log records.
    
    This filter extracts the request_id from the request state if available
    and adds it to the log record for correlation.
    """
    
    def filter(self, record):
        """
        Add request_id to the log record if available in the current context.
        
        Args:
            record: Log record
            
        Returns:
            bool: Always True (the record is always logged)
        """
        record.request_id = getattr(record, "request_id", "no-request-id")
        return True

class JsonFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    This formatter outputs log records as JSON objects with standardized fields,
    making them easier to parse and analyze in log management systems.
    """
    
    def format(self, record):
        """
        Format the log record as a JSON object.
        
        Args:
            record: Log record
            
        Returns:
            str: JSON-formatted log record
        """
        log_object = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "request_id": getattr(record, "request_id", "no-request-id")
        }
        
        # Add exception info if present
        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_object)

def setup_logging(level=logging.INFO):
    """
    Set up structured logging with request ID correlation.
    
    Args:
        level: Logging level (default: INFO)
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JsonFormatter())
    
    # Add request ID filter
    request_id_filter = RequestIdFilter()
    console_handler.addFilter(request_id_filter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Set up specific loggers
    for logger_name in ["uvicorn", "uvicorn.access", "fastapi"]:
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        logger.propagate = True

def get_logger(name: str):
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger: Configured logger
    """
    return logging.getLogger(name)

def log_with_request_id(logger, level, msg, request: Optional[Request] = None, **kwargs):
    """
    Log a message with the request ID from the request if available.
    
    Args:
        logger: Logger instance
        level: Log level
        msg: Log message
        request: FastAPI request object (optional)
        **kwargs: Additional log record arguments
    """
    extra = kwargs.pop("extra", {})
    
    if request:
        request_id = getattr(request.state, "request_id", "no-request-id")
        extra["request_id"] = request_id
    
    logger.log(level, msg, extra=extra, **kwargs)
