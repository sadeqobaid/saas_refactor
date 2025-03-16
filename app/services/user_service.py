"""
User service module for the SaaS Platform.

This module contains service functions for user-related operations.
"""

import datetime
import logging
from fastapi import HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session

from app.models import User, RefreshToken, PasswordResetToken, Tenant, TenantStatus, ActivityType
from app.utils.auth import validate_password, hash_password, verify_password, create_access_token, create_refresh_token
from app.utils.email import send_reset_email
from app.dependencies import record_user_activity, get_tenant_config
from app.config import settings

# Set up logging
logger = logging.getLogger(__name__)

def register_user(
    db: Session, 
    email: str, 
    password: str, 
    tenant_id: int,
    request: Request = None
):
    """
    Register a new user.
    
    Args:
        db: Database session
        email: User email
        password: User password
        tenant_id: Tenant ID
        request: FastAPI request object (optional)
        
    Returns:
        User: Created user
        
    Raises:
        HTTPException: If email already exists or password is invalid
    """
    # Check if email already exists in this tenant
    existing_user = db.query(User).filter(
        User.email == email,
        User.tenant_id == tenant_id
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered in this tenant")
    
    # Validate password
    validate_password(password)
    
    # Hash password and create user
    hashed_password = hash_password(password)
    new_user = User(
        email=email, 
        password_hash=hashed_password,
        tenant_id=tenant_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Record registration activity
    record_user_activity(
        db=db,
        user_id=new_user.id,
        tenant_id=tenant_id,
        activity_type=ActivityType.REGISTER.value,
        request=request
    )
    
    logger.info(f"New user registered: {email} in tenant {tenant_id}")
    return new_user


def authenticate_user(
    db: Session, 
    email: str, 
    password: str, 
    tenant_id: int,
    request: Request = None
):
    """
    Authenticate a user and generate tokens.
    
    Args:
        db: Database session
        email: User email
        password: User password
        tenant_id: Tenant ID
        request: FastAPI request object (optional)
        
    Returns:
        dict: Access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Verify the user's credentials
    user = db.query(User).filter(
        User.email == email,
        User.tenant_id == tenant_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify the password
    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Record login activity
    record_user_activity(
        db=db,
        user_id=user.id,
        tenant_id=tenant_id,
        activity_type=ActivityType.LOGIN.value,
        request=request
    )

    # Generate tokens
    access_token_expires = datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "tenant_id": str(tenant_id)}, 
        expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token = create_refresh_token(user.id, db)

    # Return the tokens
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


def request_password_reset(
    db: Session, 
    email: str, 
    tenant_id: int,
    request: Request = None,
    background_tasks: BackgroundTasks = None
):
    """
    Request a password reset.
    
    Args:
        db: Database session
        email: User email
        tenant_id: Tenant ID
        request: FastAPI request object (optional)
        background_tasks: FastAPI background tasks (optional)
        
    Returns:
        bool: True if request was successful
    """
    # Find user
    user = db.query(User).filter(
        User.email == email,
        User.tenant_id == tenant_id
    ).first()
    
    if not user:
        # Return success even if user doesn't exist to prevent email enumeration
        return True
    
    # Get tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        logger.error(f"Tenant {tenant_id} not found for password reset")
        return False
    
    # Generate a reset token
    import uuid
    token_value = str(uuid.uuid4())
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    
    # Store token in database
    reset_token = PasswordResetToken(
        token=token_value,
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(reset_token)
    db.commit()
    
    # Record password reset request activity
    record_user_activity(
        db=db,
        user_id=user.id,
        tenant_id=tenant_id,
        activity_type=ActivityType.PASSWORD_RESET.value,
        request=request,
        details="Password reset requested"
    )
    
    # Get tenant-specific frontend URL if configured
    frontend_url = get_tenant_config(
        db, 
        tenant_id, 
        "frontend_url", 
        settings.FRONTEND_URL
    )
    
    # Send reset email in background
    if background_tasks:
        background_tasks.add_task(
            send_reset_email, 
            email=user.email, 
            reset_token=token_value,
            frontend_url=frontend_url,
            tenant_name=tenant.name
        )
    
    return True


def reset_password(
    db: Session, 
    token: str, 
    new_password: str,
    request: Request = None
):
    """
    Reset password using a token.
    
    Args:
        db: Database session
        token: Password reset token
        new_password: New password
        request: FastAPI request object (optional)
        
    Returns:
        bool: True if password was reset successfully
        
    Raises:
        HTTPException: If token is invalid or password is invalid
    """
    # Find token in database
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.used == False
    ).first()
    
    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    # Check if token is expired
    if reset_token.expires_at < datetime.datetime.utcnow():
        reset_token.used = True
        db.commit()
        raise HTTPException(status_code=400, detail="Token has expired")
    
    # Get user and tenant info
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant or (tenant.status != TenantStatus.ACTIVE.value and tenant.status != TenantStatus.TRIAL.value):
        raise HTTPException(status_code=403, detail="Tenant is not active")
    
    # Validate new password
    validate_password(new_password)
    
    # Update user's password
    user.password_hash = hash_password(new_password)
    
    # Record password reset completion activity
    record_user_activity(
        db=db,
        user_id=user.id,
        tenant_id=user.tenant_id,
        activity_type=ActivityType.PASSWORD_RESET.value,
        request=request,
        details="Password reset completed"
    )
    
    # Mark token as used
    reset_token.used = True
    
    # Revoke all refresh tokens for this user
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update({"revoked": True})
    
    db.commit()
    
    return True
