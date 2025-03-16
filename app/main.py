"""
Main application module for the SaaS Platform.

This module initializes the FastAPI application and includes all routes and middleware.
"""

import datetime
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from app.config import settings
from app.db.database import engine, Base
from app.routes import tenant_router, auth_router, stats_router
from app.middleware import APITrackingMiddleware, RequestIDMiddleware
from app.utils.auth import cleanup_expired_tokens
from app.db.database import SessionLocal
from app.utils.logging import setup_logging, get_logger

# Set up structured logging with request ID correlation
setup_logging(level=logging.INFO)
logger = get_logger(__name__)

# Import error handling utilities
from app.utils.error_handling import setup_error_handlers

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-tenant SaaS Platform API",
    version="1.0.0",
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# Set up error handlers with request ID correlation
setup_error_handlers(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(APITrackingMiddleware)

# Include routers
app.include_router(auth_router)
app.include_router(tenant_router)
app.include_router(stats_router)

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    # Check database connection
    db_status = "healthy"
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check Redis connection if available
    redis_status = "not configured"
    try:
        from app.utils.auth import redis_client, redis_available
        if redis_available:
            redis_client.ping()
            redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    is_healthy = db_status == "healthy"
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "components": {
            "database": db_status,
            "redis": redis_status
        }
    }

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Multi-tenant SaaS Platform API"}

# On startup, run maintenance tasks
@app.on_event("startup")
def startup_event():
    # Run cleanup task in the main thread (not ideal but works without Celery)
    try:
        db = SessionLocal()
        cleanup_expired_tokens(db)
        db.close()
        logger.info("Expired tokens cleaned up on startup")
    except Exception as e:
        logger.error(f"Error cleaning up tokens on startup: {e}")

# Enhance OpenAPI documentation
def enhance_openapi_docs():
    """Enhance OpenAPI documentation with additional information"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = app.openapi()
    
    # Add security schemes
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}
    
    openapi_schema["components"]["securitySchemes"]["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"bearerAuth": []}]
    
    # Add tenant header parameter to all operations
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            if "parameters" not in operation:
                operation["parameters"] = []
            
            operation["parameters"].append({
                "name": "X-Tenant-ID",
                "in": "header",
                "description": "Tenant identifier",
                "required": False,
                "schema": {
                    "type": "string"
                }
            })
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Generate and cache the enhanced OpenAPI schema
app.openapi_schema = enhance_openapi_docs()