"""
Authentication utilities for the SaaS Platform.

This module contains functions for authentication, token management,
and password handling.
"""

import datetime
import uuid
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import redis
import logging
from passlib.context import CryptContext
from password_strength import PasswordPolicy

from app.config import settings
from app.db.database import get_db
from app.models import User, RefreshToken, PasswordResetToken, Tenant, TenantStatus

# Set up logging
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Password policy
password_policy = PasswordPolicy.from_names(
    length=8,  # min length
    uppercase=1,  # need min. 1 uppercase letters
    numbers=1,  # need min. 1 digits
    special=1,  # need min. 1 special characters
)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Redis connection for token blacklist
try:
    redis_client = redis.from_url(settings.REDIS_URL)
    redis_available = True
except redis.exceptions.ConnectionError:
    logger.warning("Redis connection failed. Token blacklisting will use in-memory storage.")
    redis_available = False
    # Fallback to in-memory token blacklist
    token_blacklist = {}


def blacklist_token(token: str, expires_in_seconds: int):
    """
    Add a token to the blacklist with expiration.
    
    Args:
        token: The JWT token to blacklist
        expires_in_seconds: Time in seconds until the token expires
    """
    if redis_available:
        redis_client.setex(f"blacklist:{token}", expires_in_seconds, 1)
    else:
        # In-memory fallback with expiration time
        expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in_seconds)
        token_blacklist[token] = expiry


def is_token_blacklisted(token: str) -> bool:
    """
    Check if a token is in the blacklist.
    
    Args:
        token: The JWT token to check
        
    Returns:
        bool: True if token is blacklisted, False otherwise
    """
    if redis_available:
        return bool(redis_client.exists(f"blacklist:{token}"))
    else:
        # Clean up expired tokens from in-memory blacklist
        now = datetime.datetime.utcnow()
        expired_tokens = [t for t, exp in token_blacklist.items() if exp <= now]
        for t in expired_tokens:
            token_blacklist.pop(t, None)
        
        # Check if token is in blacklist
        return token in token_blacklist


def cleanup_expired_tokens(db: Session):
    """
    Clean up expired refresh tokens from the database.
    
    Args:
        db: SQLAlchemy database session
    """
    now = datetime.datetime.utcnow()
    db.query(RefreshToken).filter(RefreshToken.expires_at < now).delete()
    db.query(PasswordResetToken).filter(PasswordResetToken.expires_at < now).delete()
    db.commit()


def create_access_token(data: dict, expires_delta: datetime.timedelta):
    """
    Create a new JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: int, db: Session):
    """
    Create a new refresh token and store it in the database.
    
    Args:
        user_id: ID of the user
        db: SQLAlchemy database session
        
    Returns:
        str: Encoded JWT refresh token
    """
    # Generate a unique token
    token_value = str(uuid.uuid4())
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Store in database
    refresh_token = RefreshToken(
        token=token_value,
        user_id=user_id,
        expires_at=expires_at
    )
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    
    # Create JWT with token ID
    token_data = {
        "sub": str(user_id),
        "jti": token_value,
        "type": "refresh"
    }
    return jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str, token_type: str, db: Session):
    """
    Verify a JWT token and return the associated user.
    
    Args:
        token: JWT token to verify
        token_type: Type of token ("access" or "refresh")
        db: SQLAlchemy database session
        
    Returns:
        User: The user associated with the token
        RefreshToken: The refresh token object (only for refresh tokens)
        
    Raises:
        HTTPException: If token is invalid, expired, or revoked
    """
    # Check if token is blacklisted
    if is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token has been revoked")
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Verify token type
        if payload.get("type") != token_type:
            raise HTTPException(status_code=401, detail=f"Invalid token type. Expected {token_type}")
        
        # For access tokens
        if token_type == "access":
            user_id = payload.get("sub")
            tenant_id = payload.get("tenant_id")
            
            if user_id is None or tenant_id is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            user = db.query(User).filter(User.id == int(user_id), User.tenant_id == int(tenant_id)).first()
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            
            # Check if tenant is active
            tenant = db.query(Tenant).filter(Tenant.id == int(tenant_id)).first()
            if not tenant or (tenant.status != TenantStatus.ACTIVE.value and tenant.status != TenantStatus.TRIAL.value):
                raise HTTPException(status_code=403, detail="Tenant is not active")
            
            return user
        
        # For refresh tokens
        elif token_type == "refresh":
            user_id = payload.get("sub")
            token_jti = payload.get("jti")
            
            if not user_id or not token_jti:
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            
            # Verify token exists in database and is not revoked
            db_token = db.query(RefreshToken).filter(
                RefreshToken.token == token_jti,
                RefreshToken.revoked == False
            ).first()
            
            if not db_token:
                raise HTTPException(status_code=401, detail="Invalid or revoked refresh token")
            
            # Check if token is expired
            if db_token.expires_at < datetime.datetime.utcnow():
                db_token.revoked = True
                db.commit()
                raise HTTPException(status_code=401, detail="Refresh token expired")
            
            user = db.query(User).filter(User.id == int(user_id)).first()
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            
            # Check if tenant is active
            tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
            if not tenant or (tenant.status != TenantStatus.ACTIVE.value and tenant.status != TenantStatus.TRIAL.value):
                raise HTTPException(status_code=403, detail="Tenant is not active")
            
            return user, db_token
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Dependency to get the current authenticated user.
    
    Args:
        token: JWT access token from request
        db: SQLAlchemy database session
        
    Returns:
        User: The authenticated user
    """
    return verify_token(token, "access", db)


def validate_password(password: str):
    """
    Validate password against policy.
    
    Args:
        password: Password to validate
        
    Raises:
        HTTPException: If password does not meet requirements
    """
    validation_errors = password_policy.test(password)
    if validation_errors:
        error_messages = []
        for error in validation_errors:
            if error.__class__.__name__ == 'Length':
                error_messages.append("Password must be at least 8 characters long")
            elif error.__class__.__name__ == 'UppercaseLetters':
                error_messages.append("Password must contain at least 1 uppercase letter")
            elif error.__class__.__name__ == 'Numbers':
                error_messages.append("Password must contain at least 1 number")
            elif error.__class__.__name__ == 'Special':
                error_messages.append("Password must contain at least 1 special character")
        
        raise HTTPException(
            status_code=400, 
            detail={"message": "Password does not meet complexity requirements", "errors": error_messages}
        )


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        bool: True if password matches hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)
