"""
Package initialization for the SaaS Platform.

This module imports and exports all components to provide a clean import interface.
"""

from .config import settings
from .db import Base, engine, SessionLocal, get_db
from .models import (
    Tenant, TenantConfig, TenantStatus,
    User, UserRole, RefreshToken, PasswordResetToken,
    UserActivity, ActivityType, MonthlyActiveUsers, UsageSummary
)
from .schemas import (
    TenantCreate, TenantUpdate, TenantResponse, TenantConfigCreate, TenantConfigResponse,
    UserRegister, UserResponse, TokenResponse, PasswordResetRequest, PasswordResetVerify, 
    PasswordReset, RefreshTokenRequest, UserActivityResponse, UserActivityHistoryResponse,
    MonthlyActiveUsersItem, MonthlyActiveUsersResponse, UsageStatisticsItem, UsageStatisticsResponse,
    TenantStatisticsSummary, TenantDetail, TenantStatisticsResponse, GlobalMAUItem, GlobalMAUResponse
)
from .utils import (
    pwd_context, password_policy, oauth2_scheme, blacklist_token, is_token_blacklisted,
    cleanup_expired_tokens, create_access_token, create_refresh_token, verify_token,
    get_current_user, validate_password, hash_password, verify_password, send_reset_email
)
from .dependencies import (
    get_tenant_slug, get_tenant_from_db, get_tenant_config, set_tenant_config,
    role_required, record_user_activity, update_usage_statistics, update_monthly_active_users
)
from .middleware import APITrackingMiddleware, RequestIDMiddleware
from .routes import tenant_router, auth_router, stats_router
from .main import app

__all__ = [
    "app",
    "settings",
    "Base", "engine", "SessionLocal", "get_db",
    "Tenant", "TenantConfig", "TenantStatus",
    "User", "UserRole", "RefreshToken", "PasswordResetToken",
    "UserActivity", "ActivityType", "MonthlyActiveUsers", "UsageSummary",
    "TenantCreate", "TenantUpdate", "TenantResponse", "TenantConfigCreate", "TenantConfigResponse",
    "UserRegister", "UserResponse", "TokenResponse", "PasswordResetRequest", "PasswordResetVerify", 
    "PasswordReset", "RefreshTokenRequest", "UserActivityResponse", "UserActivityHistoryResponse",
    "MonthlyActiveUsersItem", "MonthlyActiveUsersResponse", "UsageStatisticsItem", "UsageStatisticsResponse",
    "TenantStatisticsSummary", "TenantDetail", "TenantStatisticsResponse", "GlobalMAUItem", "GlobalMAUResponse",
    "pwd_context", "password_policy", "oauth2_scheme", "blacklist_token", "is_token_blacklisted",
    "cleanup_expired_tokens", "create_access_token", "create_refresh_token", "verify_token",
    "get_current_user", "validate_password", "hash_password", "verify_password", "send_reset_email",
    "get_tenant_slug", "get_tenant_from_db", "get_tenant_config", "set_tenant_config",
    "role_required", "record_user_activity", "update_usage_statistics", "update_monthly_active_users",
    "APITrackingMiddleware", "RequestIDMiddleware",
    "tenant_router", "auth_router", "stats_router"
]
