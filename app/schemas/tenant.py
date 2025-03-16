"""
Pydantic schemas for tenant-related data.

This module contains the Pydantic models for request and response validation
related to tenant operations.
"""

from datetime import datetime
from typing import Optional, Any, List
from pydantic import BaseModel

from app.models.tenant import TenantStatus


class TenantCreate(BaseModel):
    """Schema for creating a new tenant."""
    name: str
    slug: str
    status: TenantStatus = TenantStatus.ACTIVE


class TenantUpdate(BaseModel):
    """Schema for updating an existing tenant."""
    name: Optional[str] = None
    status: Optional[TenantStatus] = None


class TenantResponse(BaseModel):
    """Schema for tenant response data."""
    id: int
    name: str
    slug: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class TenantConfigCreate(BaseModel):
    """Schema for creating a tenant configuration."""
    key: str
    value: Any


class TenantConfigResponse(BaseModel):
    """Schema for tenant configuration response data."""
    key: str
    value: Any

    class Config:
        orm_mode = True
