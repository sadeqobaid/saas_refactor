"""
Tenant dependencies for the SaaS Platform.

This module contains dependency functions for tenant-related operations.
"""

from fastapi import Depends, Header, Query, HTTPException
from sqlalchemy.orm import Session
import json
from typing import Optional, Any

from app.db.database import get_db
from app.models import Tenant, TenantConfig, TenantStatus


def get_tenant_slug(
    x_tenant_id: Optional[str] = Header(None),
    tenant: Optional[str] = Query(None)
) -> str:
    """
    Dependency to get tenant slug from header or query parameter.
    
    Args:
        x_tenant_id: Tenant identifier from X-Tenant-ID header
        tenant: Tenant identifier from query parameter
        
    Returns:
        str: Tenant slug
        
    Raises:
        HTTPException: If tenant identifier is not provided
    """
    tenant_slug = x_tenant_id or tenant
    if not tenant_slug:
        raise HTTPException(
            status_code=400,
            detail="Tenant identifier is required. Provide either 'X-Tenant-ID' header or 'tenant' query parameter."
        )
    return tenant_slug


def get_tenant_from_db(
    tenant_slug: str = Depends(get_tenant_slug),
    db: Session = Depends(get_db)
) -> Tenant:
    """
    Dependency to get tenant from database based on slug.
    
    Args:
        tenant_slug: Tenant slug
        db: SQLAlchemy database session
        
    Returns:
        Tenant: Tenant object
        
    Raises:
        HTTPException: If tenant is not found or not active
    """
    tenant = db.query(Tenant).filter(Tenant.slug == tenant_slug).first()
    if not tenant:
        raise HTTPException(
            status_code=404,
            detail=f"Tenant '{tenant_slug}' not found"
        )
    
    # Check if tenant is active
    if tenant.status != TenantStatus.ACTIVE.value and tenant.status != TenantStatus.TRIAL.value:
        raise HTTPException(
            status_code=403,
            detail=f"Tenant '{tenant_slug}' is not active"
        )
    
    return tenant


def get_tenant_config(db: Session, tenant_id: int, key: str, default_value: Any = None) -> Any:
    """
    Get tenant configuration value.
    
    Args:
        db: SQLAlchemy database session
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


def set_tenant_config(db: Session, tenant_id: int, key: str, value: Any) -> TenantConfig:
    """
    Set tenant configuration value.
    
    Args:
        db: SQLAlchemy database session
        tenant_id: Tenant ID
        key: Configuration key
        value: Configuration value
        
    Returns:
        TenantConfig: Updated or created configuration object
    """
    # Convert value to JSON string if it's not a string
    if not isinstance(value, str):
        value = json.dumps(value)
    
    config = db.query(TenantConfig).filter(
        TenantConfig.tenant_id == tenant_id,
        TenantConfig.key == key
    ).first()
    
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
