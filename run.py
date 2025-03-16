"""
Entry point for the SaaS Platform application.

This file serves as the entry point for running the application.
"""

import uvicorn
from app.main import app
from app.utils.logging import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    logger.info("Starting SaaS Platform application")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
