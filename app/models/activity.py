"""
Activity tracking models for the SaaS Platform.

This module contains the SQLAlchemy models for tracking user activity and usage.
"""

import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func, distinct, extract, Index
from sqlalchemy.orm import relationship
from enum import Enum

from app.db.database import Base


class ActivityType(str, Enum):
    """Enum for activity type values."""
    LOGIN = "login"
    REGISTER = "register"
    PASSWORD_RESET = "password_reset"
    TOKEN_REFRESH = "token_refresh"
    API_ACCESS = "api_access"
    LOGOUT = "logout"


class UserActivity(Base):
    """
    UserActivity model for tracking user actions in the system.
    
    Used for audit trails, usage statistics, and security monitoring.
    """
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    activity_type = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    details = Column(Text, nullable=True)  # JSON string for additional details
    
    # Relationships
    user = relationship("User", back_populates="user_activities")
    tenant = relationship("Tenant")
    
    # Table arguments with composite indexes for common queries
    __table_args__ = (
        # Composite index for tenant and timestamp for activity reports
        Index('idx_user_activity_tenant_timestamp', tenant_id, timestamp),
        # Composite index for user and timestamp for user activity history
        Index('idx_user_activity_user_timestamp', user_id, timestamp),
        # Composite index for tenant, activity type and timestamp for activity type reports
        Index('idx_user_activity_tenant_type_timestamp', tenant_id, activity_type, timestamp),
        # Expression indexes for date-based queries
        Index('idx_activity_year_month', 
              extract('year', timestamp),
              extract('month', timestamp)),
    )
    
    def __repr__(self):
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, activity_type='{self.activity_type}', timestamp='{self.timestamp}')>"


class MonthlyActiveUsers(Base):
    """
    MonthlyActiveUsers model for tracking monthly active user counts per tenant.
    
    Used for billing, analytics, and tenant health monitoring.
    """
    __tablename__ = "monthly_active_users"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)
    active_users_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant")
    
    # Composite unique constraint for tenant_id, year, and month
    __table_args__ = (
        # Unique constraint
        Index('uix_mau_tenant_year_month', tenant_id, year, month, unique=True),
        # Composite index for tenant_id, year, month for MAU queries
        Index('idx_mau_tenant_year_month', tenant_id, year, month),
    )
    
    def __repr__(self):
        return f"<MonthlyActiveUsers(tenant_id={self.tenant_id}, year={self.year}, month={self.month}, count={self.active_users_count})>"


class UsageSummary(Base):
    """
    UsageSummary model for aggregating usage statistics.
    
    Used for billing, analytics, and tenant health monitoring.
    """
    __tablename__ = "usage_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)
    day = Column(Integer, nullable=True, index=True)  # Null for monthly summaries
    activity_type = Column(String, nullable=False, index=True)
    count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant")
    
    # Composite unique constraint
    __table_args__ = (
        # Unique constraint
        Index('uix_usage_tenant_date_activity', tenant_id, year, month, day, activity_type, unique=True),
        # Composite index for tenant_id, year, month, day, activity_type for usage queries
        Index('idx_usage_tenant_date_activity', tenant_id, year, month, day, activity_type),
        # Composite index for tenant_id, activity_type for activity type summaries
        Index('idx_usage_tenant_activity', tenant_id, activity_type),
    )
    
    def __repr__(self):
        return f"<UsageSummary(tenant_id={self.tenant_id}, year={self.year}, month={self.month}, day={self.day}, activity_type='{self.activity_type}', count={self.count})>"
