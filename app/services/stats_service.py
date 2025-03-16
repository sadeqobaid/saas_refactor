"""
Statistics service module for the SaaS Platform.

This module contains service functions for statistics and analytics operations.
"""

import logging
import datetime
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

from app.models import (
    User, 
    Tenant, 
    UserActivity, 
    MonthlyActiveUsers, 
    UsageSummary, 
    TenantStatus
)

# Set up logging
logger = logging.getLogger(__name__)

def get_monthly_active_users(db: Session, tenant_id: int, limit: int = 12):
    """
    Get Monthly Active Users statistics for a tenant.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        limit: Maximum number of months to return
        
    Returns:
        list: List of MAU statistics
    """
    mau_stats = db.query(MonthlyActiveUsers).filter(
        MonthlyActiveUsers.tenant_id == tenant_id
    ).order_by(
        MonthlyActiveUsers.year.desc(),
        MonthlyActiveUsers.month.desc()
    ).limit(limit).all()
    
    result = []
    for stat in mau_stats:
        result.append({
            "year": stat.year,
            "month": stat.month,
            "active_users": stat.active_users_count,
            "updated_at": stat.updated_at.isoformat()
        })
    
    return result

def get_usage_statistics(
    db: Session, 
    tenant_id: int, 
    activity_type: str = None,
    year: int = None,
    month: int = None,
    limit: int = 100
):
    """
    Get usage statistics for a tenant.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        activity_type: Type of activity to filter by (optional)
        year: Year to filter by (optional)
        month: Month to filter by (optional)
        limit: Maximum number of records to return
        
    Returns:
        list: List of usage statistics
    """
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
    usage_stats = query.limit(limit).all()
    
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
    
    return result

def get_user_activity_history(db: Session, user_id: int, tenant_id: int, limit: int = 50):
    """
    Get activity history for a specific user.
    
    Args:
        db: Database session
        user_id: User ID
        tenant_id: Tenant ID
        limit: Maximum number of activities to return
        
    Returns:
        dict: User activities
    """
    # Check if user exists and belongs to the tenant
    user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tenant_id
    ).first()
    
    if not user:
        return None
    
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

def get_tenant_statistics(db: Session):
    """
    Get statistics for all tenants.
    
    Args:
        db: Database session
        
    Returns:
        dict: Tenant statistics
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

def get_global_mau_statistics(db: Session, year: int = None, month: int = None, limit: int = 12):
    """
    Get global MAU statistics across all tenants.
    
    Args:
        db: Database session
        year: Year to filter by (optional)
        month: Month to filter by (optional)
        limit: Maximum number of months to return
        
    Returns:
        list: Global MAU statistics
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
    mau_stats = query.limit(limit).all()
    
    result = []
    for stat in mau_stats:
        result.append({
            "year": stat.year,
            "month": stat.month,
            "total_active_users": stat.total_active_users
        })
    
    return result
