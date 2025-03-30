"""
Authentication routes for the SaaS Platform.

This module contains the API routes for authentication and user management.
"""

import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Form
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional

from app.db.database import get_db
from app.models import User, Tenant, UserRole, ActivityType, TenantStatus
from app.schemas import (
    UserRegister, 
    TokenResponse, 
    PasswordResetRequest, 
    PasswordResetVerify, 
    PasswordReset,
    PasswordChangeRequest,
    RefreshTokenRequest
)
from app.dependencies import (
    get_tenant_from_db, 
    get_tenant_config, 
    record_user_activity
)
from app.utils.auth import (
    validate_password, 
    hash_password, 
    verify_password,
    create_access_token, 
    create_refresh_token, 
    verify_token,
    blacklist_token
)
from app.utils.email import send_reset_email
from app.config import settings

# Create router
router = APIRouter(tags=["authentication"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Define OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Token data model
class TokenData(BaseModel):
    username: Optional[str] = None

# Function to get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Retrieve the current authenticated user from the JWT token.
    
    Args:
        token: JWT token from the Authorization header
        db: Database session
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If the token is invalid or the user is not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    # Fetch the user from the database
    user = db.query(User).filter(User.id == int(token_data.username)).first()
    if user is None:
        raise credentials_exception
    return user


@router.post("/register")
@limiter.limit("5/minute")
def register_user(
    request: Request, 
    user_data: UserRegister, 
    tenant: Tenant = Depends(get_tenant_from_db),
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    Args:
        request: FastAPI request object
        user_data: User registration data
        tenant: Current tenant
        db: Database session
        
    Returns:
        dict: Success message
    """
    # Check if email already exists in this tenant
    existing_user = db.query(User).filter(
        User.email == user_data.email,
        User.tenant_id == tenant.id
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered in this tenant")
    
    # Validate password
    validate_password(user_data.password)
    
    # Hash password and create user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email, 
        password_hash=hashed_password,
        tenant_id=tenant.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Record registration activity
    record_user_activity(
        db=db,
        user_id=new_user.id,
        tenant_id=tenant.id,
        activity_type=ActivityType.REGISTER.value,
        request=request
    )
    
    return {"message": "User registered successfully"}


@router.post("/token", response_model=TokenResponse)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    tenant: Tenant = Depends(get_tenant_from_db),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Authenticate user and return access and refresh tokens.
    
    Args:
        form_data: OAuth2 form data with username and password
        tenant: Current tenant
        db: Database session
        request: FastAPI request object
        
    Returns:
        TokenResponse: Access and refresh tokens
    """
    # Verify the user's credentials
    user = db.query(User).filter(
        User.email == form_data.username,
        User.tenant_id == tenant.id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify the password
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Record login activity
    record_user_activity(
        db=db,
        user_id=user.id,
        tenant_id=tenant.id,
        activity_type=ActivityType.LOGIN.value,
        request=request
    )

    # Generate tokens
    access_token_expires = datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "tenant_id": str(tenant.id)}, 
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


@router.post("/refresh-token", response_model=TokenResponse)
def refresh_access_token(
    refresh_request: RefreshTokenRequest, 
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Refresh access token using a refresh token.
    
    Args:
        refresh_request: Refresh token request
        db: Database session
        request: FastAPI request object
        
    Returns:
        TokenResponse: New access and refresh tokens
    """
    # Verify refresh token
    try:
        user, db_token = verify_token(refresh_request.refresh_token, "refresh", db)
        
        # Record token refresh activity
        record_user_activity(
            db=db,
            user_id=user.id,
            tenant_id=user.tenant_id,
            activity_type=ActivityType.TOKEN_REFRESH.value,
            request=request
        )
        
        # Revoke the used refresh token
        db_token.revoked = True
        db.commit()
        
        # Generate new access token
        access_token_expires = datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "tenant_id": str(user.tenant_id)}, 
            expires_delta=access_token_expires
        )
        
        # Generate new refresh token
        new_refresh_token = create_refresh_token(user.id, db)
        
        # Return new tokens
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except HTTPException:
        # Re-raise HTTP exceptions with their original status codes and details
        raise
    except JWTError as e:
        # Handle JWT-specific errors
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        # Log the specific error for debugging
        import logging
        logging.error(f"Error refreshing token: {str(e)}")
        # Return a more specific error message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error refreshing token: {str(e)}"
        )


@router.post("/reset-password/request")
@limiter.limit("3/hour")
def reset_password_request(
    request: Request, 
    request_data: PasswordResetRequest, 
    tenant: Tenant = Depends(get_tenant_from_db),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Request a password reset.
    
    Args:
        request: FastAPI request object
        request_data: Password reset request data
        tenant: Current tenant
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        dict: Success message
    """
    user = db.query(User).filter(
        User.email == request_data.email,
        User.tenant_id == tenant.id
    ).first()
    
    if not user:
        # Return success even if user doesn't exist to prevent email enumeration
        return {"message": "If your email is registered, you will receive a password reset link"}
    
    # Generate a reset token
    import uuid
    token_value = str(uuid.uuid4())
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    
    # Store token in database
    from app.models import PasswordResetToken
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
        tenant_id=tenant.id,
        activity_type=ActivityType.PASSWORD_RESET.value,
        request=request,
        details="Password reset requested"
    )
    
    # Get tenant-specific frontend URL if configured
    frontend_url = get_tenant_config(
        db, 
        tenant.id, 
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
    
    return {"message": "If your email is registered, you will receive a password reset link"}


@router.post("/reset-password/verify")
def verify_reset_token(
    token_data: PasswordResetVerify, 
    db: Session = Depends(get_db)
):
    """
    Verify a password reset token.
    
    Args:
        token_data: Token verification data
        db: Database session
        
    Returns:
        dict: Success message
    """
    from app.models import PasswordResetToken
    
    # Find token in database
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token_data.token,
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
    
    return {"message": "Token is valid"}


@router.post("/reset-password/reset")
def reset_password(
    reset_data: PasswordReset, 
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Reset password using a token.
    
    Args:
        reset_data: Password reset data
        db: Database session
        request: FastAPI request object
        
    Returns:
        dict: Success message
    """
    from app.models import PasswordResetToken, RefreshToken
    
    # Find token in database
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == reset_data.token,
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
    validate_password(reset_data.new_password)
    
    # Update user's password
    user.password_hash = hash_password(reset_data.new_password)
    
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
    
    return {"message": "Password has been reset successfully"}


@router.post("/change-password")
def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Change user's password.
    
    Args:
        password_data: Password change data with current and new password
        current_user: Current authenticated user
        db: Database session
        request: FastAPI request object
        
    Returns:
        dict: Success message
    """
    from app.models import RefreshToken
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Validate new password
    validate_password(password_data.new_password)
    
    # Check that new password is different from current
    if verify_password(password_data.new_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="New password must be different from current password")
    
    # Update user's password
    current_user.password_hash = hash_password(password_data.new_password)
    
    # Record password change activity
    record_user_activity(
        db=db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        activity_type=ActivityType.PASSWORD_CHANGE.value,
        request=request,
        details="Password changed"
    )
    
    # Revoke all refresh tokens for this user
    db.query(RefreshToken).filter(RefreshToken.user_id == current_user.id).update({"revoked": True})
    
    db.commit()
    
    return {"message": "Password has been changed successfully"}


@router.post("/logout")
def logout(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Logout user by blacklisting their token.
    
    Args:
        token: JWT token
        db: Database session
        request: FastAPI request object
        
    Returns:
        dict: Success message
    """
    try:
        # Decode token to get expiration
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp = payload.get("exp", 0)
        current_time = datetime.datetime.utcnow().timestamp()
        
        # Calculate remaining time
        remaining_seconds = max(0, int(exp - current_time))
        
        # Add to blacklist with expiration
        blacklist_token(token, remaining_seconds)
        
        # If this is a user with a session, also invalidate their refresh tokens
        if payload.get("type") == "access" and payload.get("sub") and payload.get("tenant_id"):
            user_id = payload.get("sub")
            tenant_id = payload.get("tenant_id")
            
            user = db.query(User).filter(
                User.id == int(user_id),
                User.tenant_id == int(tenant_id)
            ).first()
            
            if user:
                # Record logout activity
                record_user_activity(
                    db=db,
                    user_id=int(user_id),
                    tenant_id=int(tenant_id),
                    activity_type=ActivityType.LOGOUT.value,
                    request=request
                )
                
                # Revoke all refresh tokens
                from app.models import RefreshToken
                db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update({"revoked": True})
                db.commit()
        
        return {"message": "Successfully logged out"}
    except Exception as e:
        # Still blacklist the token even if we can't decode it
        blacklist_token(token, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        return {"message": "Successfully logged out"}
