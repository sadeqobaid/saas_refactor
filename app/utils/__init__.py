"""
Utilities package initialization.

This module imports and exports all utility functions to provide a clean import interface.
"""

from .auth import (
    pwd_context, 
    password_policy, 
    oauth2_scheme,
    blacklist_token, 
    is_token_blacklisted, 
    cleanup_expired_tokens,
    create_access_token, 
    create_refresh_token, 
    verify_token,
    get_current_user, 
    validate_password,
    hash_password,
    verify_password
)
from .email import send_reset_email
from .logging import (
    setup_logging,
    get_logger,
    log_with_request_id,
    RequestIdFilter,
    JsonFormatter
)
from .error_handling import (
    validation_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler,
    setup_error_handlers
)

__all__ = [
    # Authentication utilities
    "pwd_context",
    "password_policy",
    "oauth2_scheme",
    "blacklist_token",
    "is_token_blacklisted",
    "cleanup_expired_tokens",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "get_current_user",
    "validate_password",
    "hash_password",
    "verify_password",
    
    # Email utilities
    "send_reset_email",
    
    # Logging utilities
    "setup_logging",
    "get_logger",
    "log_with_request_id",
    "RequestIdFilter",
    "JsonFormatter",
    
    # Error handling utilities
    "validation_exception_handler",
    "sqlalchemy_exception_handler",
    "general_exception_handler",
    "setup_error_handlers"
]
