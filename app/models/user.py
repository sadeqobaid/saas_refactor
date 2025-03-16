"""
User models for the SaaS Platform.

This module contains the SQLAlchemy models for user-related data.
"""

import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from enum import Enum

from app.db.database import Base


class UserRole(str, Enum):
    """Enum for user role values."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    BASIC_USER = "basic_user"


class User(Base):
    """
    User model representing a user in the multi-tenant system.
    
    Each user belongs to a specific tenant and has a role that determines their permissions.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default=UserRole.BASIC_USER.value, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Composite unique constraint for email and tenant_id
    __table_args__ = (
        UniqueConstraint("email", "tenant_id", name="uix_user_email_tenant"),
        # Composite index for tenant_id and role for admin queries
        Index("idx_user_tenant_role", "tenant_id", "role"),
    )
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    user_activities = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}', tenant_id={self.tenant_id})>"


class RefreshToken(Base):
    """
    RefreshToken model for storing JWT refresh tokens.
    
    Used for issuing new access tokens without requiring re-authentication.
    """
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
    
    # Table arguments with partial index for non-revoked tokens
    __table_args__ = (
        # Partial index for valid tokens
        Index("idx_valid_refresh_tokens", "user_id", "expires_at", postgresql_where=(revoked == False)),
    )
    
    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at='{self.expires_at}', revoked={self.revoked})>"


class PasswordResetToken(Base):
    """
    PasswordResetToken model for storing password reset tokens.
    
    Used for the password reset flow.
    """
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    used = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="password_reset_tokens")
    
    # Table arguments with partial index for unused tokens
    __table_args__ = (
        # Partial index for unused tokens
        Index("idx_valid_reset_tokens", "user_id", "expires_at", postgresql_where=(used == False)),
    )
    
    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, expires_at='{self.expires_at}', used={self.used})>"