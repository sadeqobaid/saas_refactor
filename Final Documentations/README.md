# SaaS Refactor Project

A multi-tenant SaaS platform with authentication, user management, and analytics capabilities.

## Overview

This project is a Software as a Service (SaaS) platform that supports multiple tenants with isolated data and user management. It provides a robust authentication system, user activity tracking, and analytics features.

## Features

- **Multi-tenancy**: Complete isolation of data between different tenants
- **Authentication**: Secure JWT-based authentication with refresh tokens
- **User Management**: User registration, login, password reset, and password change
- **Activity Tracking**: Comprehensive logging of user activities
- **Analytics**: Usage statistics and monthly active user tracking
- **Admin Dashboard**: Tenant and user management for administrators
- **Super Admin**: Cross-tenant visibility and management capabilities
- **Streamlit Frontend**: User-friendly interface for all functionality

## Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Frontend**: Streamlit
- **Authentication**: JWT with refresh tokens
- **Caching**: Redis for token blacklisting

## Project Structure

```
saas_refactor/
├── app/
│   ├── config/         # Configuration settings
│   ├── db/             # Database connection and models
│   ├── dependencies/   # FastAPI dependencies
│   ├── models/         # SQLAlchemy models
│   ├── routes/         # API endpoints
│   ├── schemas/        # Pydantic schemas
│   ├── utils/          # Utility functions
│   └── main.py         # FastAPI application entry point
├── streamlit_app.py    # Streamlit frontend application
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/sadeqobaid/saas_refactor.git
   cd saas_refactor
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up PostgreSQL database:
   - Create a PostgreSQL database
   - Run the database script to create tables and initial data:
     ```
     psql -U postgres -d postgres -f fixed_database_script.sql
     ```

5. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update the values in `.env` with your configuration

## Running the Application

1. Start the FastAPI backend:
   ```
   uvicorn app.main:app --reload
   ```

2. Start the Streamlit frontend:
   ```
   streamlit run streamlit_app.py
   ```

3. Access the application:
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Streamlit Frontend: http://localhost:8501

## Default Users

The system comes with two default users:

1. Super Admin:
   - Email: admin@example.com
   - Password: Admin@123
   - Tenant: System Admin

2. Tenant Admin:
   - Email: tenant@example.com
   - Password: Admin@123
   - Tenant: Default Tenant

## API Endpoints

### Authentication

- `POST /register`: Register a new user
- `POST /token`: Login and get access token
- `POST /refresh-token`: Refresh access token
- `POST /reset-password/request`: Request password reset
- `POST /reset-password/verify`: Verify reset token
- `POST /reset-password/reset`: Reset password with token
- `POST /change-password`: Change user password
- `POST /logout`: Logout and invalidate tokens

### Statistics

- `GET /admin/stats/mau`: Get Monthly Active Users statistics
- `GET /admin/stats/usage`: Get usage statistics
- `GET /admin/stats/user-activity/{user_id}`: Get user activity history
- `GET /admin/stats/super-admin/tenants`: Get tenant statistics (super admin only)
- `GET /admin/stats/super-admin/global-mau`: Get global MAU statistics (super admin only)

## License

This project is proprietary and confidential.

## Author

Sadeq A. Obaid
