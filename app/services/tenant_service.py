"""
Tenant service module for the SaaS Platform.

This module contains service functions for tenant-related operations.
"""

import logging
import json
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Tenant, TenantConfig, User, UserRole

# Set up logging
logger = logging.getLogger(__name__)

def create_tenant(db: Session, name: str, slug: str, status: str):
    """
    Create a new tenant.
    
    Args:
        db: Database session
        name: Tenant name
        slug: Tenant slug (unique identifier)
        status: Tenant status
        
    Returns:
        Tenant: Created tenant
        
    Raises:
        HTTPException: If tenant slug already exists
    """
    # Check if tenant slug already exists
    existing_tenant = db.query(Tenant).filter(Tenant.slug == slug).first()
    if existing_tenant:
        raise HTTPException(status_code=400, detail="Tenant slug already exists")
    
    # Create new tenant
    new_tenant = Tenant(
        name=name,
        slug=slug,
        status=status
    )
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    
    logger.info(f"New tenant created: {name} ({slug})")
    return new_tenant

def update_tenant(db: Session, tenant_id: int, name: str = None, status: str = None):
    """
    Update tenant details.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        name: New tenant name (optional)
        status: New tenant status (optional)
        
    Returns:
        Tenant: Updated tenant
        
    Raises:
        HTTPException: If tenant is not found
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Update fields if provided
    if name is not None:
        tenant.name = name
    if status is not None:
        tenant.status = status
    
    import datetime
    tenant.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(tenant)
    
    logger.info(f"Tenant updated: {tenant.name} ({tenant.slug})")
    return tenant

def get_tenant_config(db: Session, tenant_id: int, key: str, default_value=None):
    """
    Get tenant configuration value.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        key: Configuration key
        default_value: Default value if key is not found
        
    Returns:
        Any: Configuration value
    """
    config = db.query(TenantConfig).filter(
        TenantConfig.tenant_id == tenant_id,
        TenantConfig.key == key
    ).first()
    
    if not config:
        return default_value
    
    try:
        # Try to parse as JSON
        return json.loads(config.value)
    except (json.JSONDecodeError, TypeError):
        # Return as string if not valid JSON
        return config.value

def set_tenant_config(db: Session, tenant_id: int, key: str, value):
    """
    Set tenant configuration value.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        key: Configuration key
        value: Configuration value
        
    Returns:
        TenantConfig: Updated or created configuration object
        
    Raises:
        HTTPException: If tenant is not found
    """
    # Check if tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Convert value to JSON string if it's not a string
    if not isinstance(value, str):
        value = json.dumps(value)
    
    config = db.query(TenantConfig).filter(
        TenantConfig.tenant_id == tenant_id,
        TenantConfig.key == key
    ).first()
    
    import datetime
    if config:
        config.value = value
        config.updated_at = datetime.datetime.utcnow()
    else:
        config = TenantConfig(
            tenant_id=tenant_id,
            key=key,
            value=value
        )
        db.add(config)
    
    db.commit()
    db.refresh(config)
    return config

def check_tenant_access(db: Session, user: User, tenant_id: int, admin_required: bool = False):
    """
    Check if a user has access to a tenant.
    
    Args:
        db: Database session
        user: User object
        tenant_id: Tenant ID
        admin_required: Whether admin access is required
        
    Returns:
        bool: True if user has access
        
    Raises:
        HTTPException: If user does not have access
    """
    # Super admins have access to all tenants
    if user.role == UserRole.SUPER_ADMIN.value:
        return True
    
    # Check if user belongs to this tenant
    if user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    # Check if admin access is required
    if admin_required and user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return True
