"""
Configuration package for the SaaS Platform.
"""

from .config import settings, SECRET_KEY, ALGORITHM, SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM

__all__ = [
    "settings", 
    "SECRET_KEY", 
    "ALGORITHM", 
    "SMTP_SERVER", 
    "SMTP_PORT", 
    "SMTP_USERNAME", 
    "SMTP_PASSWORD", 
    "EMAIL_FROM"
]
