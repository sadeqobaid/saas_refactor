"""
Services package initialization.

This module imports and exports all service functions to provide a clean import interface.
"""

from .user_service import (
    register_user,
    authenticate_user,
    request_password_reset,
    reset_password
)
from .tenant_service import (
    create_tenant,
    update_tenant,
    get_tenant_config,
    set_tenant_config,
    check_tenant_access
)
from .stats_service import (
    get_monthly_active_users,
    get_usage_statistics,
    get_user_activity_history,
    get_tenant_statistics,
    get_global_mau_statistics
)

__all__ = [
    # User services
    "register_user",
    "authenticate_user",
    "request_password_reset",
    "reset_password",
    
    # Tenant services
    "create_tenant",
    "update_tenant",
    "get_tenant_config",
    "set_tenant_config",
    "check_tenant_access",
    
    # Statistics services
    "get_monthly_active_users",
    "get_usage_statistics",
    "get_user_activity_history",
    "get_tenant_statistics",
    "get_global_mau_statistics"
]
