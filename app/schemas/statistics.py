"""
Statistics schemas for the SaaS Platform.

This module contains the Pydantic models for request and response validation
related to usage statistics and analytics.
"""

from typing import List, Optional
from pydantic import BaseModel


class MonthlyActiveUsersItem(BaseModel):
    """Schema for monthly active users statistics item."""
    year: int
    month: int
    active_users: int
    updated_at: str


class MonthlyActiveUsersResponse(BaseModel):
    """Schema for monthly active users statistics response."""
    mau_statistics: List[MonthlyActiveUsersItem]


class UsageStatisticsItem(BaseModel):
    """Schema for usage statistics item."""
    year: int
    month: int
    day: Optional[int] = None
    activity_type: str
    count: int
    updated_at: str


class UsageStatisticsResponse(BaseModel):
    """Schema for usage statistics response."""
    usage_statistics: List[UsageStatisticsItem]


class TenantStatisticsSummary(BaseModel):
    """Schema for tenant statistics summary."""
    total_tenants: int
    active_tenants: int
    trial_tenants: int
    inactive_tenants: int
    suspended_tenants: int


class TenantDetail(BaseModel):
    """Schema for tenant detail in statistics."""
    id: int
    name: str
    slug: str
    status: str
    created_at: str
    user_count: int


class TenantStatisticsResponse(BaseModel):
    """Schema for tenant statistics response."""
    summary: TenantStatisticsSummary
    tenants: List[TenantDetail]


class GlobalMAUItem(BaseModel):
    """Schema for global monthly active users item."""
    year: int
    month: int
    total_active_users: int


class GlobalMAUResponse(BaseModel):
    """Schema for global monthly active users response."""
    global_mau_statistics: List[GlobalMAUItem]
