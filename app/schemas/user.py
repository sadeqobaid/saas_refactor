"""
Pydantic schemas for user-related data.

This module contains the Pydantic models for request and response validation
related to user operations.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, validator

from app.models.user import UserRole


class UserRegister(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str
    
    @validator('password')
    def password_validation(cls, v):
        # Password validation will be handled in the service layer
        return v


class UserResponse(BaseModel):
    """Schema for user response data."""
    id: int
    email: str
    role: str
    tenant_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class PasswordResetVerify(BaseModel):
    """Schema for password reset token verification."""
    token: str


class PasswordReset(BaseModel):
    """Schema for password reset with new password."""
    token: str
    new_password: str
    
    @validator('new_password')
    def password_validation(cls, v):
        # Password validation will be handled in the service layer
        return v


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


class UserActivityResponse(BaseModel):
    """Schema for user activity response data."""
    activity_type: str
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[str] = None

    class Config:
        orm_mode = True


class UserActivityHistoryResponse(BaseModel):
    """Schema for user activity history response."""
    user_id: int
    email: str
    activities: List[UserActivityResponse]
