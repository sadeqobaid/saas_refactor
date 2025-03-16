"""
Middleware for the SaaS Platform.

This module contains middleware components for request processing.
"""

import jwt
import logging
from fastapi import Request
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.db.database import SessionLocal
from app.models import User
from app.dependencies.user import record_user_activity

# Set up logging
logger = logging.getLogger(__name__)

class APITrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track API access for analytics and monitoring.
    
    This middleware records successful API calls to the user_activities table.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and track successful API calls.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response: The response from the next middleware or route handler
        """
        # Process the request
        response = await call_next(request)
        
        # Only track successful API calls
        if response.status_code < 400 and request.url.path != "/":
            # Skip tracking for certain endpoints like health checks
            if not request.url.path.startswith(("/docs", "/openapi", "/redoc")):
                try:
                    # Get user ID if authenticated
                    user_id = None
                    tenant_id = None
                    auth_header = request.headers.get("Authorization")
                    
                    if auth_header and auth_header.startswith("Bearer "):
                        token = auth_header.replace("Bearer ", "")
                        try:
                            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                            if payload.get("type") == "access":
                                user_id = payload.get("sub")
                                tenant_id = payload.get("tenant_id")
                                
                                if user_id and tenant_id:
                                    # Get DB session
                                    db = SessionLocal()
                                    try:
                                        user = db.query(User).filter(
                                            User.id == int(user_id),
                                            User.tenant_id == int(tenant_id)
                                        ).first()
                                        
                                        if user:
                                            # Record API access
                                            record_user_activity(
                                                db=db,
                                                user_id=int(user_id),
                                                tenant_id=int(tenant_id),
                                                activity_type="api_access",
                                                request=request,
                                                details=f"Path: {request.url.path}"
                                            )
                                    finally:
                                        db.close()
                        except:
                            # If token is invalid, just continue without tracking
                            pass
                except Exception as e:
                    logger.error(f"Error tracking API access: {str(e)}")
        
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add a unique request ID to each request for tracing.
    
    This middleware adds a unique ID to each request and response for tracing purposes.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and add a unique request ID.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response: The response from the next middleware or route handler
        """
        import uuid
        
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Process the request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
