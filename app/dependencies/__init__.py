"""
Dependencies package initialization.

This module imports and exports all dependency functions to provide a clean import interface.
"""

from .tenant import (
    get_tenant_slug,
    get_tenant_from_db,
    get_tenant_config,
    set_tenant_config
)
from .user import (
    role_required,
    record_user_activity,
    update_usage_statistics,
    update_monthly_active_users
)

__all__ = [
    # Tenant dependencies
    "get_tenant_slug",
    "get_tenant_from_db",
    "get_tenant_config",
    "set_tenant_config",
    
    # User dependencies
    "role_required",
    "record_user_activity",
    "update_usage_statistics",
    "update_monthly_active_users"
]
