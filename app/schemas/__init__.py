"""
Schemas package initialization.

This module imports and exports all schemas to provide a clean import interface.
"""

from .tenant import (
    TenantCreate, 
    TenantUpdate, 
    TenantResponse, 
    TenantConfigCreate, 
    TenantConfigResponse
)
from .user import (
    UserRegister, 
    UserResponse, 
    TokenResponse, 
    PasswordResetRequest, 
    PasswordResetVerify, 
    PasswordReset, 
    RefreshTokenRequest,
    UserActivityResponse,
    UserActivityHistoryResponse
)
from .statistics import (
    MonthlyActiveUsersItem,
    MonthlyActiveUsersResponse,
    UsageStatisticsItem,
    UsageStatisticsResponse,
    TenantStatisticsSummary,
    TenantDetail,
    TenantStatisticsResponse,
    GlobalMAUItem,
    GlobalMAUResponse
)

__all__ = [
    # Tenant schemas
    "TenantCreate", 
    "TenantUpdate", 
    "TenantResponse", 
    "TenantConfigCreate", 
    "TenantConfigResponse",
    
    # User schemas
    "UserRegister", 
    "UserResponse", 
    "TokenResponse", 
    "PasswordResetRequest", 
    "PasswordResetVerify", 
    "PasswordReset", 
    "RefreshTokenRequest",
    "UserActivityResponse",
    "UserActivityHistoryResponse",
    
    # Statistics schemas
    "MonthlyActiveUsersItem",
    "MonthlyActiveUsersResponse",
    "UsageStatisticsItem",
    "UsageStatisticsResponse",
    "TenantStatisticsSummary",
    "TenantDetail",
    "TenantStatisticsResponse",
    "GlobalMAUItem",
    "GlobalMAUResponse"
]
