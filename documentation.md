# SaaS Platform Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Setup Instructions](#setup-instructions)
4. [Running the Application](#running-the-application)
5. [API Endpoints](#api-endpoints)
6. [Multi-tenancy Implementation](#multi-tenancy-implementation)
7. [Authentication and Security](#authentication-and-security)
8. [Traceability Features](#traceability-features)
9. [Troubleshooting](#troubleshooting)

## Project Overview

This project is a multi-tenant SaaS platform built with FastAPI for the backend API and Streamlit for the frontend GUI. The application provides user authentication, tenant management, and usage statistics tracking.

The codebase has been refactored to improve:
- Readability through modular organization
- Traceability with request ID tracking and structured logging
- Maintainability with separation of concerns
- Documentation with comprehensive comments and guides

## Project Structure

```
saas_refactor/
├── app/                  # Backend API application
│   ├── config/           # Configuration settings
│   ├── db/               # Database connection
│   ├── dependencies/     # FastAPI dependencies
│   ├── middleware/       # Custom middleware
│   ├── models/           # Database models
│   ├── routes/           # API endpoints
│   ├── schemas/          # Data validation
│   ├── services/         # Business logic
│   ├── utils/            # Utility functions
│   ├── __init__.py       
│   ├── api_documentation.py
│   └── main.py           # API entry point
├── README.md             # Project documentation
├── run.py                # Backend runner
├── streamlit_app.py      # Frontend Streamlit GUI
├── todo.md               # Project tasks
└── validate.py           # Validation script
```

### Key Components

#### Models
- `tenant.py`: Tenant and TenantConfig models
- `user.py`: User, RefreshToken, and PasswordResetToken models
- `activity.py`: Activity tracking models

#### Schemas
- `tenant.py`: Tenant request/response schemas
- `user.py`: User authentication schemas
- `statistics.py`: Statistics response schemas

#### Routes
- `tenant.py`: Tenant management endpoints
- `auth.py`: Authentication endpoints
- `stats.py`: Statistics endpoints

#### Services
- `user_service.py`: User business logic
- `tenant_service.py`: Tenant business logic
- `stats_service.py`: Statistics business logic

#### Middleware
- `middleware.py`: Request ID and API tracking middleware

#### Utilities
- `auth.py`: Authentication utilities
- `email.py`: Email sending utilities
- `logging.py`: Structured logging with request ID correlation
- `error_handling.py`: Centralized error handling

## Setup Instructions

### Step 1: Extract the zip file
1. Download the `saas_refactored_updated.zip` file to your desktop
2. Right-click on the zip file and select "Extract All..." or use your preferred extraction tool
3. Extract it to a location of your choice (e.g., your desktop)
4. You should now have a folder named `saas_refactor` containing all the code

### Step 2: Set up the Python environment
1. Open a terminal/command prompt
2. Navigate to the extracted folder:
   ```
   cd path/to/saas_refactor
   ```
3. Create a virtual environment:
   ```
   python -m venv venv
   ```
4. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

### Step 3: Install dependencies
1. With the virtual environment activated, install the required packages:
   ```
   pip install fastapi uvicorn sqlalchemy pydantic python-jose[cryptography] passlib python-multipart redis python-dotenv slowapi email-validator streamlit requests
   ```

### Step 4: Set up the database
1. Install PostgreSQL if not already installed
2. Create a new PostgreSQL database:
   ```
   createdb saas_platform
   ```
3. Create a `.env` file in the `saas_refactor` directory with the following content:
   ```
   DATABASE_URL=postgresql://username:password@localhost/saas_platform
   REDIS_URL=redis://localhost:6379/0
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ```
   (Replace `username` and `password` with your PostgreSQL credentials)

## Running the Application

### Running the Backend API
1. Make sure you're in the `saas_refactor` directory with the virtual environment activated
2. Run the backend API:
   ```
   python run.py
   ```
3. The API should start and be available at http://127.0.0.1:8000
4. You can access the API documentation at http://127.0.0.1:8000/docs

### Running the Streamlit Frontend
1. Open a new terminal/command prompt window
2. Navigate to the `saas_refactor` directory
3. Activate the virtual environment (as in Step 2.4 of Setup)
4. Run the Streamlit app:
   ```
   streamlit run streamlit_app.py
   ```
5. The Streamlit app should open in your browser at http://localhost:8501

### Using the Application
The Streamlit interface provides the following functionality:
- Register a new user
- Log in with existing credentials
- Reset your password
- Access the dashboard (when logged in)
- Change your password (when logged in)
- Log out

## API Endpoints

### Authentication Endpoints
- `POST /register`: Register a new user
- `POST /token`: Login and get access token
- `POST /refresh-token`: Refresh an access token
- `POST /logout`: Logout and invalidate token
- `POST /reset-password/request`: Request password reset
- `POST /reset-password/verify`: Verify reset token
- `POST /reset-password/reset`: Reset password with token

### Tenant Endpoints
- `POST /tenants`: Create a new tenant (super admin only)
- `GET /tenants`: List all tenants (super admin only)
- `GET /tenants/{tenant_id}`: Get tenant details (super admin only)
- `PUT /tenants/{tenant_id}`: Update tenant (super admin only)

### Tenant Configuration Endpoints
- `POST /tenants/{tenant_id}/config`: Create/update tenant config
- `GET /tenants/{tenant_id}/config/{key}`: Get tenant config value
- `GET /tenants/{tenant_id}/config`: List all tenant configs

### Statistics Endpoints
- `GET /admin/stats/mau`: Get Monthly Active Users statistics
- `GET /admin/stats/usage`: Get usage statistics
- `GET /admin/stats/user-activity/{user_id}`: Get user activity history
- `GET /super-admin/stats/tenants`: Get tenant statistics (super admin only)
- `GET /super-admin/stats/global-mau`: Get global MAU statistics (super admin only)

### User Management Endpoints
- `POST /admin/users/bulk-create`: Bulk create users (admin only)

### Health Check Endpoint
- `GET /health`: Check API health status
- `GET /`: Root endpoint

## Multi-tenancy Implementation

The application implements multi-tenancy with the following features:

1. **Tenant Identification**: Tenants are identified via the `X-Tenant-ID` header or `tenant` query parameter.

2. **Tenant Isolation**: Data is isolated at the row level with tenant_id foreign keys.

3. **Tenant Configuration**: Each tenant can have custom configurations stored in the `tenant_configs` table.

4. **Tenant-Specific Authentication**: Authentication tokens include tenant information.

5. **Tenant Status Management**: Tenants can be in different states (active, inactive, suspended, trial).

## Authentication and Security

The application implements the following security features:

1. **Password Hashing**: Passwords are hashed using bcrypt.

2. **Password Policy**: Passwords must meet complexity requirements:
   - Minimum 8 characters
   - At least 1 uppercase letter
   - At least 1 number
   - At least 1 special character

3. **JWT Authentication**: JSON Web Tokens are used for authentication.

4. **Token Refresh**: Access tokens can be refreshed using refresh tokens.

5. **Token Blacklisting**: Revoked tokens are blacklisted to prevent reuse.

6. **Role-Based Access Control**: Different user roles (super_admin, admin, basic_user) have different permissions.

## Traceability Features

The application includes the following traceability features:

1. **Request ID Tracking**: Each request is assigned a unique ID that is propagated through all logs.

2. **Structured Logging**: Logs are formatted as JSON with request ID correlation.

3. **Centralized Error Handling**: All errors are handled centrally with request ID correlation.

4. **User Activity Tracking**: All user activities are recorded with timestamps and IP addresses.

5. **Usage Statistics**: Usage statistics are aggregated for reporting.

## Troubleshooting

### Common Issues

#### Database Connection Issues
- Ensure PostgreSQL is running
- Verify the credentials in the `.env` file are correct
- Check that the database exists

#### Import Errors
- Make sure all dependencies are installed correctly
- Verify the virtual environment is activated

#### API Startup Issues
- Check for error messages in the terminal
- Ensure the required ports (8000 for API, 8501 for Streamlit) are available

#### Authentication Issues
- Ensure the `SECRET_KEY` in the `.env` file is set
- Check that the tenant is active
- Verify user credentials

### Getting Help
If you encounter issues not covered in this documentation, please:
1. Check the logs for error messages
2. Run the validation script: `python validate.py`
3. Consult the API documentation at http://127.0.0.1:8000/docs
