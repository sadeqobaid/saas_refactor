"""
User dependencies for the SaaS Platform.

This module contains dependency functions for user-related operations.
"""

import datetime
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import User, UserRole
from app.utils.auth import get_current_user


def role_required(required_roles: list[UserRole]):
    """
    Dependency factory to check if the current user has one of the required roles.
    
    Args:
        required_roles: List of roles that are allowed to access the endpoint
        
    Returns:
        Callable: Dependency function that returns the current user if authorized
        
    Raises:
        HTTPException: If user does not have the required role
    """
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in [role.value for role in required_roles]:
            raise HTTPException(status_code=403, detail="Access forbidden")
        return current_user
    return role_checker


def record_user_activity(
    db: Session, 
    user_id: int, 
    tenant_id: int,
    activity_type: str, 
    request = None, 
    details: str = None
):
    """
    Record user activity for tracking purposes.
    
    Args:
        db: SQLAlchemy database session
        user_id: User ID
        tenant_id: Tenant ID
        activity_type: Type of activity
        request: FastAPI request object (optional)
        details: Additional details (optional)
    """
    from app.models import UserActivity
    
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
    
    activity = UserActivity(
        user_id=user_id,
        tenant_id=tenant_id,
        activity_type=activity_type,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details
    )
    
    db.add(activity)
    db.commit()
    
    # Update usage statistics in the same request
    update_usage_statistics(db, tenant_id, activity_type)
    
    # Update MAU if this is a login activity
    if activity_type == "login":
        update_monthly_active_users(db, tenant_id)


def update_usage_statistics(db: Session, tenant_id: int, activity_type: str):
    """
    Update usage statistics for tenant and activity type.
    
    Args:
        db: SQLAlchemy database session
        tenant_id: Tenant ID
        activity_type: Type of activity
    """
    from app.models import UsageSummary
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        now = datetime.datetime.utcnow()
        year, month, day = now.year, now.month, now.day
        
        # Update daily summary
        daily_summary = db.query(UsageSummary).filter(
            UsageSummary.tenant_id == tenant_id,
            UsageSummary.year == year,
            UsageSummary.month == month,
            UsageSummary.day == day,
            UsageSummary.activity_type == activity_type
        ).first()
        
        if daily_summary:
            daily_summary.count += 1
            daily_summary.updated_at = now
        else:
            daily_summary = UsageSummary(
                tenant_id=tenant_id,
                year=year,
                month=month,
                day=day,
                activity_type=activity_type,
                count=1
            )
            db.add(daily_summary)
        
        # Update monthly summary
        monthly_summary = db.query(UsageSummary).filter(
            UsageSummary.tenant_id == tenant_id,
            UsageSummary.year == year,
            UsageSummary.month == month,
            UsageSummary.day == None,
            UsageSummary.activity_type == activity_type
        ).first()
        
        if monthly_summary:
            monthly_summary.count += 1
            monthly_summary.updated_at = now
        else:
            monthly_summary = UsageSummary(
                tenant_id=tenant_id,
                year=year,
                month=month,
                day=None,
                activity_type=activity_type,
                count=1
            )
            db.add(monthly_summary)
        
        db.commit()
        logger.info(f"Usage statistics updated for tenant {tenant_id}, activity {activity_type}")
    except Exception as e:
        logger.error(f"Error updating usage statistics: {e}")
        db.rollback()


def update_monthly_active_users(db: Session, tenant_id: int):
    """
    Update Monthly Active Users count for a tenant.
    
    Args:
        db: SQLAlchemy database session
        tenant_id: Tenant ID
    """
    from app.models import MonthlyActiveUsers, UserActivity
    from sqlalchemy import func, distinct
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        now = datetime.datetime.utcnow()
        year, month = now.year, now.month
        
        # Get the count of unique users who had activity this month
        start_of_month = datetime.datetime(year, month, 1)
        end_of_month = (start_of_month.replace(month=month+1, day=1) if month < 12 
                        else start_of_month.replace(year=year+1, month=1, day=1)) - datetime.timedelta(days=1)
        
        active_users_count = db.query(func.count(distinct(UserActivity.user_id))).filter(
            UserActivity.tenant_id == tenant_id,
            UserActivity.timestamp >= start_of_month,
            UserActivity.timestamp <= end_of_month
        ).scalar()
        
        # Update or create MAU record
        mau_record = db.query(MonthlyActiveUsers).filter(
            MonthlyActiveUsers.tenant_id == tenant_id,
            MonthlyActiveUsers.year == year,
            MonthlyActiveUsers.month == month
        ).first()
        
        if mau_record:
            mau_record.active_users_count = active_users_count
            mau_record.updated_at = now
        else:
            mau_record = MonthlyActiveUsers(
                tenant_id=tenant_id,
                year=year,
                month=month,
                active_users_count=active_users_count
            )
            db.add(mau_record)
        
        db.commit()
        logger.info(f"MAU updated for tenant {tenant_id}: {active_users_count} active users")
    except Exception as e:
        logger.error(f"Error updating MAU: {e}")
        db.rollback()
