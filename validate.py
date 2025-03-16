"""
Validation script for the SaaS Platform.

This script performs basic validation checks to ensure the refactored code
is working correctly.
"""

import sys
import logging
import requests
from fastapi.testclient import TestClient

from app.main import app
from app.utils.logging import setup_logging, get_logger

# Set up logging
setup_logging(level=logging.INFO)
logger = get_logger(__name__)

# Create test client
client = TestClient(app)

def test_health_endpoint():
    """Test the health check endpoint."""
    logger.info("Testing health endpoint")
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data
    assert "database" in data["components"]
    logger.info("Health endpoint test passed")
    return True

def test_root_endpoint():
    """Test the root endpoint."""
    logger.info("Testing root endpoint")
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    logger.info("Root endpoint test passed")
    return True

def test_request_id_middleware():
    """Test the request ID middleware."""
    logger.info("Testing request ID middleware")
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    request_id = response.headers["X-Request-ID"]
    assert len(request_id) > 0
    logger.info(f"Request ID middleware test passed: {request_id}")
    return True

def run_all_tests():
    """Run all validation tests."""
    logger.info("Starting validation tests")
    
    tests = [
        test_health_endpoint,
        test_root_endpoint,
        test_request_id_middleware
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Test {test.__name__} failed: {str(e)}")
            failed += 1
    
    logger.info(f"Validation complete: {passed} passed, {failed} failed")
    return passed, failed

if __name__ == "__main__":
    passed, failed = run_all_tests()
    if failed > 0:
        sys.exit(1)
    sys.exit(0)
