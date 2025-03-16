import streamlit as st
import requests
import json
from datetime import datetime, timedelta

# FastAPI backend URL
FASTAPI_URL = "http://127.0.0.1:8000"

# Page title
st.title("SaaS Platform GUI")

# Initialize session state variables if they don't exist
if "token" not in st.session_state:
    st.session_state["token"] = None
if "refresh_token" not in st.session_state:
    st.session_state["refresh_token"] = None
if "token_expiry" not in st.session_state:
    st.session_state["token_expiry"] = None
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None
if "password_feedback" not in st.session_state:
    st.session_state["password_feedback"] = None

# Function to check token validity and refresh if needed
def ensure_valid_token():
    if not st.session_state["token"] or not st.session_state["refresh_token"]:
        return False
    
    # Check if token is expired or will expire soon (within 1 minute)
    if st.session_state["token_expiry"] and datetime.now() > st.session_state["token_expiry"] - timedelta(minutes=1):
        try:
            # Try to refresh the token
            response = requests.post(
                f"{FASTAPI_URL}/refresh-token",
                json={"refresh_token": st.session_state["refresh_token"]}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                st.session_state["token"] = token_data["access_token"]
                st.session_state["refresh_token"] = token_data["refresh_token"]
                # Set token expiry to current time + 30 minutes (default expiry)
                st.session_state["token_expiry"] = datetime.now() + timedelta(minutes=30)
                return True
            else:
                # If refresh fails, clear session and return False
                st.session_state["token"] = None
                st.session_state["refresh_token"] = None
                st.session_state["token_expiry"] = None
                st.session_state["logged_in"] = False
                st.session_state["user_email"] = None
                return False
        except Exception as e:
            st.error(f"Error refreshing token: {str(e)}")
            return False
    
    return True

# Function to validate password strength
def validate_password(password):
    # Check minimum length
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    # Check for uppercase
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least 1 uppercase letter"
    
    # Check for numbers
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least 1 number"
    
    # Check for special characters
    special_chars = "!@#$%^&*()-_=+[]{}|;:'\",.<>/?"
    if not any(c in special_chars for c in password):
        return False, "Password must contain at least 1 special character"
    
    return True, "Password meets all requirements"

# Sidebar for navigation
st.sidebar.title("Navigation")

# Show different navigation options based on login status
if st.session_state["logged_in"]:
    page = st.sidebar.radio("Choose a page", ["Dashboard", "Change Password", "Logout"])
    st.sidebar.markdown(f"Logged in as: **{st.session_state['user_email']}**")
else:
    page = st.sidebar.radio("Choose a page", ["Register", "Login", "Reset Password"])

# Register Page
if page == "Register":
    st.header("User Registration")
    
    with st.form("register_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        # Password strength indicator
        if password:
            is_valid, feedback = validate_password(password)
            if is_valid:
                st.success(feedback)
            else:
                st.warning(feedback)
        
        submitted = st.form_submit_button("Register")
        
        if submitted:
            if not email or not password:
                st.error("Please fill in all fields")
            else:
                try:
                    response = requests.post(
                        f"{FASTAPI_URL}/register",
                        json={"email": email, "password": password}
                    )
                    
                    if response.status_code == 200:
                        st.success("User registered successfully! You can now log in.")
                    else:
                        error_detail = "Unknown error"
                        try:
                            error_data = response.json()
                            if "detail" in error_data:
                                if isinstance(error_data["detail"], dict) and "message" in error_data["detail"]:
                                    error_detail = error_data["detail"]["message"]
                                    if "errors" in error_data["detail"]:
                                        error_detail += ":\n" + "\n".join([f"- {err}" for err in error_data["detail"]["errors"]])
                                else:
                                    error_detail = error_data["detail"]
                        except:
                            error_detail = response.text or f"Error code: {response.status_code}"
                        
                        st.error(f"Registration failed: {error_detail}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {str(e)}")

# Login Page
elif page == "Login":
    st.header("User Login")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if not email or not password:
                st.error("Please fill in all fields")
            else:
                try:
                    response = requests.post(
                        f"{FASTAPI_URL}/token",
                        data={"username": email, "password": password}
                    )
                    
                    if response.status_code == 200:
                        token_data = response.json()
                        st.session_state["token"] = token_data["access_token"]
                        st.session_state["refresh_token"] = token_data["refresh_token"]
                        st.session_state["token_expiry"] = datetime.now() + timedelta(minutes=30)
                        st.session_state["logged_in"] = True
                        st.session_state["user_email"] = email
                        st.success("Login successful!")
                        st.experimental_rerun()
                    else:
                        error_detail = "Invalid email or password"
                        try:
                            error_data = response.json()
                            if "detail" in error_data:
                                error_detail = error_data["detail"]
                        except:
                            pass
                        st.error(f"Login failed: {error_detail}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {str(e)}")

# Reset Password Flow
elif page == "Reset Password":
    st.header("Reset Password")
    
    # Create tabs for the different steps of the password reset flow
    reset_tabs = st.tabs(["Request Reset", "Verify Token", "Set New Password"])
    
    # Tab 1: Request password reset
    with reset_tabs[0]:
        with st.form("reset_request_form"):
            email = st.text_input("Email")
            submitted = st.form_submit_button("Send Reset Link")
            
            if submitted:
                if not email:
                    st.error("Please enter your email")
                else:
                    try:
                        response = requests.post(
                            f"{FASTAPI_URL}/reset-password/request",
                            json={"email": email}
                        )
                        
                        if response.status_code == 200:
                            st.success("If your email is registered, you will receive a password reset link")
                        else:
                            st.error("Failed to process request. Please try again later.")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Connection error: {str(e)}")
    
    # Tab 2: Verify reset token
    with reset_tabs[1]:
        with st.form("verify_token_form"):
            token = st.text_input("Reset Token (from email)")
            submitted = st.form_submit_button("Verify Token")
            
            if submitted:
                if not token:
                    st.error("Please enter the reset token")
                else:
                    try:
                        response = requests.post(
                            f"{FASTAPI_URL}/reset-password/verify",
                            json={"token": token}
                        )
                        
                        if response.status_code == 200:
                            st.success("Token is valid! You can now set a new password.")
                            st.session_state["reset_token"] = token
                        else:
                            error_detail = "Invalid or expired token"
                            try:
                                error_data = response.json()
                                if "detail" in error_data:
                                    error_detail = error_data["detail"]
                            except:
                                pass
                            st.error(f"Verification failed: {error_detail}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Connection error: {str(e)}")
    
    # Tab 3: Set new password
    with reset_tabs[2]:
        with st.form("reset_password_form"):
            token = st.text_input("Reset Token", value=st.session_state.get("reset_token", ""))
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            # Password strength indicator
            if new_password:
                is_valid, feedback = validate_password(new_password)
                if is_valid:
                    st.success(feedback)
                else:
                    st.warning(feedback)
            
            submitted = st.form_submit_button("Reset Password")
            
            if submitted:
                if not token or not new_password or not confirm_password:
                    st.error("Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    is_valid, feedback = validate_password(new_password)
                    if not is_valid:
                        st.error(f"Password does not meet requirements: {feedback}")
                    else:
                        try:
                            response = requests.post(
                                f"{FASTAPI_URL}/reset-password/reset",
                                json={"token": token, "new_password": new_password}
                            )
                            
                            if response.status_code == 200:
                                st.success("Password has been reset successfully! You can now log in with your new password.")
                                if "reset_token" in st.session_state:
                                    del st.session_state["reset_token"]
                            else:
                                error_detail = "Failed to reset password"
                                try:
                                    error_data = response.json()
                                    if "detail" in error_data:
                                        error_detail = error_data["detail"]
                                except:
                                    pass
                                st.error(f"Reset failed: {error_detail}")
                        except requests.exceptions.RequestException as e:
                            st.error(f"Connection error: {str(e)}")

# Dashboard Page (only visible when logged in)
elif page == "Dashboard":
    # Check token validity
    if ensure_valid_token():
        st.header("User Dashboard")
        st.write("Welcome to your dashboard!")
        
        # Example of accessing a protected endpoint
        try:
            response = requests.get(
                f"{FASTAPI_URL}/",
                headers={"Authorization": f"Bearer {st.session_state['token']}"}
            )
            
            if response.status_code == 200:
                st.json(response.json())
            else:
                st.error("Failed to fetch data from API")
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
    else:
        st.error("Your session has expired. Please log in again.")
        st.session_state["logged_in"] = False
        st.experimental_rerun()

# Change Password Page (only visible when logged in)
elif page == "Change Password":
    # Check token validity
    if ensure_valid_token():
        st.header("Change Password")
        
        with st.form("change_password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            # Password strength indicator
            if new_password:
                is_valid, feedback = validate_password(new_password)
                if is_valid:
                    st.success(feedback)
                else:
                    st.warning(feedback)
            
            submitted = st.form_submit_button("Change Password")
            
            if submitted:
                if not current_password or not new_password or not confirm_password:
                    st.error("Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("New passwords do not match")
                else:
                    is_valid, feedback = validate_password(new_password)
                    if not is_valid:
                        st.error(f"Password does not meet requirements: {feedback}")
                    else:
                        # This endpoint is not in the original API but would be a good addition
                        # For now, we'll show a message that this feature is coming soon
                        st.info("Password change functionality is coming soon!")
                        
                        # If the API had this endpoint, it would look something like:
                        """
                        try:
                            response = requests.post(
                                f"{FASTAPI_URL}/change-password",
                                headers={"Authorization": f"Bearer {st.session_state['token']}"},
                                json={
                                    "current_password": current_password,
                                    "new_password": new_password
                                }
                            )
                            
                            if response.status_code == 200:
                                st.success("Password changed successfully!")
                                # After password change, all tokens should be invalidated
                                # so we should log the user out
                                st.session_state["token"] = None
                                st.session_state["refresh_token"] = None
                                st.session_state["token_expiry"] = None
                                st.session_state["logged_in"] = False
                                st.session_state["user_email"] = None
                                st.experimental_rerun()
                            else:
                                error_detail = "Failed to change password"
                                try:
                                    error_data = response.json()
                                    if "detail" in error_data:
                                        error_detail = error_data["detail"]
                                except:
                                    pass
                                st.error(f"Password change failed: {error_detail}")
                        except requests.exceptions.RequestException as e:
                            st.error(f"Connection error: {str(e)}")
                        """
    else:
        st.error("Your session has expired. Please log in again.")
        st.session_state["logged_in"] = False
        st.experimental_rerun()

# Logout Page
elif page == "Logout":
    st.header("Logout")
    
    if st.session_state["token"]:
        try:
            response = requests.post(
                f"{FASTAPI_URL}/logout",
                headers={"Authorization": f"Bearer {st.session_state['token']}"}
            )
            
            # Clear session state regardless of response
            st.session_state["token"] = None
            st.session_state["refresh_token"] = None
            st.session_state["token_expiry"] = None
            st.session_state["logged_in"] = False
            st.session_state["user_email"] = None
            
            if response.status_code == 200:
                st.success("Logged out successfully!")
            else:
                st.warning("Logout on server failed, but you've been logged out locally.")
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
            st.warning("Could not connect to the server, but you've been logged out locally.")
    else:
        st.warning("You are not logged in.")

# Footer in the sidebar
st.sidebar.markdown("---")  # Adds a horizontal line for separation
st.sidebar.markdown("Developed by  \n\n**Sadeq A. Obaid**")
