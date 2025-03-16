"""
Email utilities for the SaaS Platform.

This module contains functions for sending emails, including password reset emails.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings

# Set up logging
logger = logging.getLogger(__name__)

def send_reset_email(email: str, reset_token: str, frontend_url: str, tenant_name: str):
    """
    Send password reset email to a user.
    
    Args:
        email: Recipient email address
        reset_token: Password reset token
        frontend_url: URL of the frontend application
        tenant_name: Name of the tenant
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Create reset link
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"
        
        # Create the email
        subject = f"Password Reset Request - {tenant_name}"
        body = f"""
        You requested a password reset for your account on {tenant_name}.
        
        Please click the link below to reset your password:
        {reset_link}
        
        This link will expire in {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes.
        
        If you did not request this reset, please ignore this email.
        """
        
        msg = MIMEMultipart()
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        # Send the email
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()  # Enable TLS encryption
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, email, msg.as_string())
        
        logger.info(f"Password reset email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
