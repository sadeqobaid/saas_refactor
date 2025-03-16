"""
Tenant routes for the SaaS Platform.

This module contains the API routes for tenant management.
"""

import datetime
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models import User, Tenant, UserRole, TenantConfig
from app.schemas import (
    TenantCreate, 
    TenantUpdate, 
    TenantResponse, 
    TenantConfigCreate, 
    TenantConfigResponse
)
from app.dependencies import role_required, get_tenant_from_db
from app.dependencies.user import get_current_user
from app.services.tenant_service import get_tenant_config, set_tenant_config

# Create router
router = APIRouter(
    prefix="/tenants",
    tags=["tenants"],
    responses={404: {"description": "Not found"}},
)


@router.post("", response_model=TenantResponse)
def create_tenant(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required([UserRole.SUPER_ADMIN]))
):
    """
    Create a new tenant (super admin only).
    
    Args:
        tenant_data: Tenant data
        db: Database session
        current_user: Current authenticated user (must be super admin)
        
    Returns:
        TenantResponse: Created tenant
    """
    # Check if tenant slug already exists
    existing_tenant = db.query(Tenant).filter(Tenant.slug == tenant_data.slug).first()
    if existing_tenant:
        raise HTTPException(status_code=400, detail="Tenant slug already exists")
    
    # Create new tenant
    new_tenant = Tenant(
        name=tenant_data.name,
        slug=tenant_data.slug,
        status=tenant_data.status
    )
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    
    return new_tenant


@router.get("", response_model=List[TenantResponse])
def list_tenants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required([UserRole.SUPER_ADMIN]))
):
    """
    List all tenants (super admin only).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user (must be super admin)
        
    Returns:
        List[TenantResponse]: List of tenants
    """
    tenants = db.query(Tenant).offset(skip).limit(limit).all()
    return tenants


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required([UserRole.SUPER_ADMIN]))
):
    """
    Get tenant details by ID (super admin only).
    
    Args:
        tenant_id: Tenant ID
        db: Database session
        current_user: Current authenticated user (must be super admin)
        
    Returns:
        TenantResponse: Tenant details
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: int,
    tenant_data: TenantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required([UserRole.SUPER_ADMIN]))
):
    """
    Update tenant details (super admin only).
    
    Args:
        tenant_id: Tenant ID
        tenant_data: Tenant data to update
        db: Database session
        current_user: Current authenticated user (must be super admin)
        
    Returns:
        TenantResponse: Updated tenant
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Update fields if provided
    if tenant_data.name is not None:
        tenant.name = tenant_data.name
    if tenant_data.status is not None:
        tenant.status = tenant_data.status
    
    tenant.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(tenant)
    
    return tenant


@router.post("/{tenant_id}/config", response_model=TenantConfigResponse)
def create_tenant_config(
    tenant_id: int,
    config_data: TenantConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required([UserRole.SUPER_ADMIN, UserRole.ADMIN]))
):
    """
    Create or update tenant configuration (admin only).
    
    Args:
        tenant_id: Tenant ID
        config_data: Configuration data
        db: Database session
        current_user: Current authenticated user (must be admin or super admin)
        
    Returns:
        TenantConfigResponse: Created or updated configuration
    """
    # Check if tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Check if user is admin of this tenant or super admin
    if current_user.role != UserRole.SUPER_ADMIN.value and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    # Set tenant config
    config = set_tenant_config(db, tenant_id, config_data.key, config_data.value)
    
    return {"key": config.key, "value": config_data.value}


@router.get("/{tenant_id}/config/{key}", response_model=TenantConfigResponse)
def get_tenant_config_value(
    tenant_id: int,
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get tenant configuration value.
    
    Args:
        tenant_id: Tenant ID
        key: Configuration key
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        TenantConfigResponse: Configuration value
    """
    # Check if tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Check if user belongs to this tenant or is super admin
    if current_user.role != UserRole.SUPER_ADMIN.value and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    # Get tenant config
    value = get_tenant_config(db, tenant_id, key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Configuration key '{key}' not found")
    
    return {"key": key, "value": value}


@router.get("/{tenant_id}/config", response_model=List[TenantConfigResponse])
def list_tenant_configs(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all tenant configurations.
    
    Args:
        tenant_id: Tenant ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[TenantConfigResponse]: List of configurations
    """
    # Check if tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Check if user belongs to this tenant or is super admin
    if current_user.role != UserRole.SUPER_ADMIN.value and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    # Get all tenant configs
    configs = db.query(TenantConfig).filter(TenantConfig.tenant_id == tenant_id).all()
    
    result = []
    for config in configs:
        try:
            value = json.loads(config.value)
        except (json.JSONDecodeError, TypeError):
            value = config.value
        
        result.append({"key": config.key, "value": value})
    
    return result
