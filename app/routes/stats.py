"""
Statistics routes for the SaaS Platform.

This module contains the API routes for usage statistics and analytics.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import Optional

from app.db.database import get_db
from app.models import (
    User, 
    Tenant, 
    UserRole, 
    UserActivity, 
    MonthlyActiveUsers, 
    UsageSummary, 
    TenantStatus
)
from app.schemas import (
    MonthlyActiveUsersResponse,
    UsageStatisticsResponse,
    TenantStatisticsResponse,
    GlobalMAUResponse
)
from app.dependencies import role_required
from app.routes.auth import get_current_user  # Import the get_current_user dependency

# Create router
router = APIRouter(
    prefix="/admin/stats",
    tags=["statistics"],
    responses={404: {"description": "Not found"}},
)


@router.get("/mau", response_model=MonthlyActiveUsersResponse)
def get_monthly_active_users(
    current_user: User = Depends(get_current_user),  # Use the get_current_user dependency
    db: Session = Depends(get_db)
):
    """
    Get Monthly Active Users statistics for the current tenant.
    
    Args:
        current_user: Current authenticated user (must be admin or super admin)
        db: Database session
        
    Returns:
        MonthlyActiveUsersResponse: MAU statistics
    """
    # Check if user is admin or super admin
    if current_user.role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    # For super admin, allow specifying tenant_id as query parameter
    tenant_id = current_user.tenant_id
    
    mau_stats = db.query(MonthlyActiveUsers).filter(
        MonthlyActiveUsers.tenant_id == tenant_id
    ).order_by(
        MonthlyActiveUsers.year.desc(),
        MonthlyActiveUsers.month.desc()
    ).limit(12).all()
    
    result = []
    for stat in mau_stats:
        result.append({
            "year": stat.year,
            "month": stat.month,
            "active_users": stat.active_users_count,
            "updated_at": stat.updated_at.isoformat()
        })
    
    return {"mau_statistics": result}


@router.get("/usage", response_model=UsageStatisticsResponse)
def get_usage_statistics(
    activity_type: str = None,
    year: int = None,
    month: int = None,
    current_user: User = Depends(get_current_user),  # Use the get_current_user dependency
    db: Session = Depends(get_db)
):
    """
    Get usage statistics filtered by activity type, year, and month for the current tenant.
    
    Args:
        activity_type: Type of activity to filter by
        year: Year to filter by
        month: Month to filter by
        current_user: Current authenticated user (must be admin or super admin)
        db: Database session
        
    Returns:
        UsageStatisticsResponse: Usage statistics
    """
    # Check if user is admin or super admin
    if current_user.role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    # For super admin, allow specifying tenant_id as query parameter
    tenant_id = current_user.tenant_id
    
    query = db.query(UsageSummary).filter(UsageSummary.tenant_id == tenant_id)
    
    # Apply filters
    if activity_type:
        query = query.filter(UsageSummary.activity_type == activity_type)
    if year:
        query = query.filter(UsageSummary.year == year)
    if month:
        query = query.filter(UsageSummary.month == month)
    
    # Order by date (most recent first)
    query = query.order_by(
        UsageSummary.year.desc(),
        UsageSummary.month.desc(),
        UsageSummary.day.desc() if UsageSummary.day is not None else UsageSummary.day
    )
    
    # Get results
    usage_stats = query.limit(100).all()
    
    result = []
    for stat in usage_stats:
        result.append({
            "year": stat.year,
            "month": stat.month,
            "day": stat.day,
            "activity_type": stat.activity_type,
            "count": stat.count,
            "updated_at": stat.updated_at.isoformat()
        })
    
    return {"usage_statistics": result}


@router.get("/user-activity/{user_id}")
def get_user_activity(
    user_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_user),  # Use the get_current_user dependency
    db: Session = Depends(get_db)
):
    """
    Get activity history for a specific user in the current tenant.
    
    Args:
        user_id: User ID
        limit: Maximum number of activities to return
        current_user: Current authenticated user (must be admin or super admin)
        db: Database session
        
    Returns:
        dict: User activities
    """
    # Check if user is admin or super admin
    if current_user.role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    # For super admin, allow specifying tenant_id as query parameter
    tenant_id = current_user.tenant_id
    
    # Check if user exists and belongs to the tenant
    user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tenant_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found in this tenant")
    
    # Get user activities
    activities = db.query(UserActivity).filter(
        UserActivity.user_id == user_id,
        UserActivity.tenant_id == tenant_id
    ).order_by(UserActivity.timestamp.desc()).limit(limit).all()
    
    result = []
    for activity in activities:
        result.append({
            "activity_type": activity.activity_type,
            "timestamp": activity.timestamp.isoformat(),
            "ip_address": activity.ip_address,
            "user_agent": activity.user_agent,
            "details": activity.details
        })
    
    return {
        "user_id": user_id,
        "email": user.email,
        "activities": result
    }


# Super Admin Statistics Endpoints
@router.get("/super-admin/tenants", response_model=TenantStatisticsResponse)
def get_tenant_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required([UserRole.SUPER_ADMIN]))
):
    """
    Get statistics for all tenants (super admin only).
    
    Args:
        db: Database session
        current_user: Current authenticated user (must be super admin)
        
    Returns:
        TenantStatisticsResponse: Tenant statistics
    """
    # Get tenant counts
    total_tenants = db.query(func.count(Tenant.id)).scalar()
    active_tenants = db.query(func.count(Tenant.id)).filter(Tenant.status == TenantStatus.ACTIVE.value).scalar()
    trial_tenants = db.query(func.count(Tenant.id)).filter(Tenant.status == TenantStatus.TRIAL.value).scalar()
    inactive_tenants = db.query(func.count(Tenant.id)).filter(Tenant.status == TenantStatus.INACTIVE.value).scalar()
    suspended_tenants = db.query(func.count(Tenant.id)).filter(Tenant.status == TenantStatus.SUSPENDED.value).scalar()
    
    # Get user counts per tenant
    tenant_user_counts = db.query(
        User.tenant_id,
        func.count(User.id).label('user_count')
    ).group_by(User.tenant_id).all()
    
    tenant_users = {}
    for tenant_id, user_count in tenant_user_counts:
        tenant_users[tenant_id] = user_count
    
    # Get tenant details with user counts
    tenants = db.query(Tenant).all()
    tenant_details = []
    
    for tenant in tenants:
        tenant_details.append({
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
            "status": tenant.status,
            "created_at": tenant.created_at.isoformat(),
            "user_count": tenant_users.get(tenant.id, 0)
        })
    
    return {
        "summary": {
            "total_tenants": total_tenants,
            "active_tenants": active_tenants,
            "trial_tenants": trial_tenants,
            "inactive_tenants": inactive_tenants,
            "suspended_tenants": suspended_tenants
        },
        "tenants": tenant_details
    }


@router.get("/super-admin/global-mau", response_model=GlobalMAUResponse)
def get_global_mau_statistics(
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required([UserRole.SUPER_ADMIN]))
):
    """
    Get global MAU statistics across all tenants (super admin only).
    
    Args:
        year: Year to filter by
        month: Month to filter by
        db: Database session
        current_user: Current authenticated user (must be super admin)
        
    Returns:
        GlobalMAUResponse: Global MAU statistics
    """
    query = db.query(
        MonthlyActiveUsers.year,
        MonthlyActiveUsers.month,
        func.sum(MonthlyActiveUsers.active_users_count).label('total_active_users')
    ).group_by(
        MonthlyActiveUsers.year,
        MonthlyActiveUsers.month
    )
    
    # Apply filters if provided
    if year:
        query = query.filter(MonthlyActiveUsers.year == year)
    if month:
        query = query.filter(MonthlyActiveUsers.month == month)
    
    # Order by date (most recent first)
    query = query.order_by(
        MonthlyActiveUsers.year.desc(),
        MonthlyActiveUsers.month.desc()
    )
    
    # Get results
    mau_stats = query.limit(12).all()
    
    result = []
    for stat in mau_stats:
        result.append({
            "year": stat.year,
            "month": stat.month,
            "total_active_users": stat.total_active_users
        })
    
    return {"global_mau_statistics": result}