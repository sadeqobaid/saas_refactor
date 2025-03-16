"""
Routes package initialization.

This module imports and exports all route handlers to provide a clean import interface.
"""

from .tenant import router as tenant_router
from .auth import router as auth_router
from .stats import router as stats_router

__all__ = [
    "tenant_router",
    "auth_router",
    "stats_router"
]
