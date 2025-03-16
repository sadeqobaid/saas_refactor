"""
Tenant models for the SaaS Platform.

This module contains the SQLAlchemy models for tenant-related data.
"""

import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, or_, UniqueConstraint
from sqlalchemy.orm import relationship
from enum import Enum

from app.db.database import Base


class TenantStatus(str, Enum):
    """Enum for tenant status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TRIAL = "trial"


class Tenant(Base):
    """
    Tenant model representing a customer organization in the multi-tenant system.
    
    Each tenant has its own users and configuration settings.
    """
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, nullable=False, default=TenantStatus.ACTIVE.value, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="tenant")
    tenant_configs = relationship("TenantConfig", back_populates="tenant", cascade="all, delete-orphan")
    
    # Table arguments with partial index for active tenants
    __table_args__ = (
        # Partial index for active and trial tenants (most commonly queried)
        Index('idx_active_tenants', id, 
              postgresql_where=or_(status == TenantStatus.ACTIVE.value, 
                                  status == TenantStatus.TRIAL.value)),
    )
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', slug='{self.slug}', status='{self.status}')>"


class TenantConfig(Base):
    """
    Tenant configuration model for storing tenant-specific settings.
    
    Each tenant can have multiple configuration key-value pairs.
    """
    __tablename__ = "tenant_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    key = Column(String, nullable=False, index=True)
    value = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Composite unique constraint for tenant_id and key
    __table_args__ = (
        UniqueConstraint('tenant_id', 'key', name='uix_tenant_config'),
        # Composite index for tenant_id and key for faster lookups
        Index('idx_tenant_config_lookup', tenant_id, key),
    )
    
    # Relationships
    tenant = relationship("Tenant", back_populates="tenant_configs")
    
    def __repr__(self):
        return f"<TenantConfig(tenant_id={self.tenant_id}, key='{self.key}')>"
