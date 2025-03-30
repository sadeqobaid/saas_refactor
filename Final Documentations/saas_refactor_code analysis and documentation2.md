# SaaS Refactor Project Code Documentation - Part 2

## Table of Contents

1. [Introduction](#introduction)
2. [Routes Folder](#routes-folder)
   - [__init__.py](#routes-init)
   - [auth.py](#routes-auth)
   - [stats.py](#routes-stats)
   - [tenant.py](#routes-tenant)
3. [Schemas Folder](#schemas-folder)
   - [__init__.py](#schemas-init)
   - [tenant.py](#schemas-tenant)
   - [user.py](#schemas-user)
   - [statistics.py](#schemas-statistics)
4. [Services Folder](#services-folder)
   - [__init__.py](#services-init)
   - [README.md](#services-readme)
   - [user_service.py](#services-user)
   - [tenant_service.py](#services-tenant)
   - [stats_service.py](#services-stats)
5. [Utils Folder](#utils-folder)
   - [__init__.py](#utils-init)
   - [auth.py](#utils-auth)
   - [email.py](#utils-email)
   - [logging.py](#utils-logging)
   - [error_handling.py](#utils-error)
6. [Conclusion](#conclusion)

## Introduction <a name="introduction"></a>

This document provides a comprehensive analysis of the SaaS Refactor project's code structure, focusing on the routes, schemas, services, and utils folders. Each script is documented with its purpose and a detailed line-by-line description of its functionality.

The SaaS Refactor project is a multi-tenant SaaS platform built with FastAPI, providing authentication, tenant management, and usage statistics features. The codebase follows a well-structured architecture with clear separation of concerns:

- **Routes**: API endpoints and request handlers
- **Schemas**: Data validation models using Pydantic
- **Services**: Business logic implementation
- **Utils**: Utility functions and helpers

This documentation aims to provide a clear understanding of how these components work together to form a cohesive application.

## Routes Folder <a name="routes-folder"></a>

The routes folder contains API endpoint definitions and request handlers for the SaaS platform.

### __init__.py <a name="routes-init"></a>

**Purpose**: This file initializes the routes package and exports all route handlers to provide a clean import interface.

**Line-by-Line Description**:
- Lines 0-4: Module docstring explaining the purpose of the file
- Line 6: Imports the tenant router from the tenant module
- Line 7: Imports the auth router from the auth module
- Line 8: Imports the stats router from the stats module
- Lines 10-14: Defines the `__all__` list which specifies all symbols that should be exported when the package is imported with a wildcard import, including all three routers

### auth.py <a name="routes-auth"></a>

**Purpose**: This file contains the API routes for authentication and user management, handling operations like user registration, login, token refresh, password reset, and logout.

**Line-by-Line Description**:
- Lines 0-4: Module docstring explaining the purpose of the file
- Line 6: Imports datetime module for timestamp handling
- Lines 7-8: Imports necessary FastAPI components for routing, dependency injection, and authentication
- Line 9: Imports SQLAlchemy Session for database operations
- Lines 10-11: Imports rate limiting functionality from slowapi
- Line 12: Imports JWT handling from jose library
- Lines 13-14: Imports Pydantic BaseModel and typing utilities
- Line 16: Imports the get_db function from the database module
- Line 17: Imports necessary models (User, Tenant, UserRole, ActivityType)
- Lines 18-25: Imports schemas for request/response validation
- Lines 26-30: Imports dependencies for tenant management and user activity tracking
- Lines 31-39: Imports authentication utilities
- Line 40: Imports email utilities for password reset
- Line 41: Imports application settings
- Line 44: Creates an APIRouter with the "authentication" tag
- Line 47: Creates a rate limiter using client IP addresses
- Line 50: Defines the OAuth2 scheme for token-based authentication
- Lines 53-54: Defines the TokenData model for JWT payload validation
- Lines 57-89: Defines the get_current_user dependency function
  - Lines 58-70: Function docstring explaining purpose, parameters, return value, and exceptions
  - Lines 71-75: Defines the credentials exception for authentication failures
  - Lines 76-81: Decodes the JWT token and extracts the username (user ID)
  - Lines 82-83: Handles JWT decoding errors
  - Lines 86-88: Fetches the user from the database and returns it
- Lines 92-144: Defines the register_user endpoint
  - Line 93: Applies rate limiting (5 requests per minute)
  - Lines 94-99: Function parameters including request, user data, tenant, and database session
  - Lines 100-111: Function docstring explaining purpose, parameters, and return value
  - Lines 113-119: Checks if the email is already registered in this tenant
  - Line 122: Validates the password against policy
  - Lines 125-133: Hashes the password, creates the user, and commits to the database
  - Lines 136-142: Records the registration activity
  - Line 144: Returns a success message
- Lines 147-211: Defines the login_for_access_token endpoint
  - Lines 149-153: Function parameters including form data, tenant, database session, and request
  - Lines 154-165: Function docstring explaining purpose, parameters, and return value
  - Lines 167-177: Verifies the user's credentials (email)
  - Lines 180-185: Verifies the user's password
  - Lines 188-194: Records the login activity
  - Lines 197-201: Generates an access token with expiration
  - Line 204: Creates a refresh token
  - Lines 207-211: Returns the tokens
- Lines 214-267: Defines the refresh_access_token endpoint
  - Lines 216-219: Function parameters including refresh request, database session, and request
  - Lines 220-230: Function docstring explaining purpose, parameters, and return value
  - Lines 233-242: Verifies the refresh token and records token refresh activity
  - Lines 245-246: Revokes the used refresh token
  - Lines 249-253: Generates a new access token
  - Line 256: Generates a new refresh token
  - Lines 259-263: Returns the new tokens
  - Lines 264-267: Handles exceptions
- Lines 270-320: Defines the reset_password_request endpoint
  - Line 271: Applies rate limiting (3 requests per hour)
  - Lines 272-278: Function parameters including request, request data, tenant, background tasks, and database session
  - Lines 279-291: Function docstring explaining purpose, parameters, and return value
  - Lines 292-299: Finds the user by email and returns a generic success message even if user doesn't exist (to prevent email enumeration)
  - Lines 302-304: Generates a reset token with expiration
  - Lines 307-314: Stores the token in the database
  - Lines 317-320: Records the password reset request activity
- Lines 323-369: Defines the verify_reset_token endpoint
  - Lines 324-328: Function parameters including token, database session
  - Lines 329-340: Function docstring explaining purpose, parameters, and return value
  - Lines 343-349: Finds the token in the database
  - Lines 352-355: Checks if the token is expired
  - Lines 358-366: Gets user and tenant info and checks if tenant is active
  - Line 368: Returns a success message
- Lines 371-426: Defines the reset_password endpoint
  - Lines 372-376: Function parameters including reset data, database session, and request
  - Lines 377-388: Function docstring explaining purpose, parameters, and return value
  - Line 390: Imports necessary models
  - Lines 393-399: Finds the token in the database
  - Lines 402-405: Checks if the token is expired
  - Lines 408-416: Gets user and tenant info and checks if tenant is active
  - Line 419: Validates the new password
  - Line 422: Updates the user's password
  - Lines 425-432: Records the password reset completion activity
  - Lines 435-436: Marks the token as used
  - Lines 439-440: Revokes all refresh tokens for this user
  - Line 442: Commits the changes to the database
  - Line 444: Returns a success message
- Lines 447-486: Defines the logout endpoint
  - Lines 448-452: Function parameters including token, database session, and request
  - Lines 453-463: Function docstring explaining purpose, parameters, and return value
  - Lines 465-470: Decodes the token to get expiration and calculates remaining time
  - Line 473: Adds the token to the blacklist with expiration
  - Lines 476-485: If the token belongs to a user, records logout activity and revokes refresh tokens
  - Line 487: Returns a success message
  - Lines 488-491: Handles exceptions by still blacklisting the token

### stats.py <a name="routes-stats"></a>

**Purpose**: This file contains the API routes for usage statistics and analytics, providing endpoints for retrieving monthly active users, usage statistics, user activity, and tenant statistics.

**Line-by-Line Description**:
- Lines 0-4: Module docstring explaining the purpose of the file
- Lines 6-9: Imports necessary FastAPI components and SQLAlchemy functions
- Line 10: Imports typing utilities
- Line 11: Imports the get_db function from the database module
- Lines 12-20: Imports necessary models for statistics
- Lines 21-26: Imports schemas for response validation
- Line 27: Imports role_required dependency for authorization
- Line 28: Imports get_current_user dependency from auth module
- Lines 31-35: Creates an APIRouter with prefix, tags, and response descriptions
- Lines 38-76: Defines the get_monthly_active_users endpoint
  - Lines 39-42: Function parameters including current user and database session
  - Lines 43-52: Function docstring explaining purpose, parameters, and return value
  - Lines 54-55: Checks if user is admin or super admin
  - Line 58: Gets tenant ID from current user
  - Lines 60-65: Queries the database for MAU statistics
  - Lines 67-74: Formats the results
  - Line 76: Returns the MAU statistics
- Lines 79-138: Defines the get_usage_statistics endpoint
  - Lines 81-86: Function parameters including filters, current user, and database session
  - Lines 87-99: Function docstring explaining purpose, parameters, and return value
  - Lines 101-102: Checks if user is admin or super admin
  - Line 105: Gets tenant ID from current user
  - Line 107: Starts building the query
  - Lines 110-115: Applies filters if provided
  - Lines 118-122: Orders the results by date
  - Line 125: Limits the results and executes the query
  - Lines 127-136: Formats the results
  - Line 138: Returns the usage statistics
- Lines 141-196: Defines the get_user_activity endpoint
  - Lines 143-147: Function parameters including user ID, limit, current user, and database session
  - Lines 148-159: Function docstring explaining purpose, parameters, and return value
  - Lines 161-162: Checks if user is admin or super admin
  - Line 165: Gets tenant ID from current user
  - Lines 168-174: Checks if the user exists and belongs to the tenant
  - Lines 177-180: Queries the database for user activities
  - Lines 182-190: Formats the results
  - Lines 192-196: Returns the user activities with user information
- Lines 199-255: Defines the get_tenant_statistics endpoint (super admin only)
  - Lines 201-204: Function parameters including database session and current user (must be super admin)
  - Lines 205-214: Function docstring explaining purpose, parameters, and return value
  - Lines 216-220: Gets tenant counts by status
  - Lines 223-230: Gets user counts per tenant
  - Lines 233-244: Gets tenant details with user counts
  - Lines 246-254: Returns the tenant statistics summary and details
- Lines 258-308: Defines the get_global_mau_statistics endpoint (super admin only)
  - Lines 260-264: Function parameters including filters, database session, and current user (must be super admin)
  - Lines 265-276: Function docstring explaining purpose, parameters, and return value
  - Lines 277-284: Builds the query for global MAU statistics
  - Lines 287-290: Applies filters if provided
  - Lines 293-296: Orders the results by date
  - Line 299: Limits the results and executes the query
  - Lines 301-307: Formats the results
  - Line 309: Returns the global MAU statistics

### tenant.py <a name="routes-tenant"></a>

**Purpose**: This file contains the API routes for tenant management, providing endpoints for creating, listing, updating, and configuring tenants.

**Line-by-Line Description**:
- Lines 0-4: Module docstring explaining the purpose of the file
- Lines 6-8: Imports datetime, json, and necessary FastAPI components
- Line 9: Imports SQLAlchemy Session for database operations
- Line 10: Imports typing utilities
- Line 12: Imports the get_db function from the database module
- Line 13: Imports necessary models (User, Tenant, UserRole, TenantConfig)
- Lines 14-20: Imports schemas for request/response validation
- Lines 21-23: Imports dependencies and services for tenant management
- Lines 26-30: Creates an APIRouter with prefix, tags, and response descriptions
- Lines 33-65: Defines the create_tenant endpoint (super admin only)
  - Lines 34-38: Function parameters including tenant data, database session, and current user (must be super admin)
  - Lines 39-49: Function docstring explaining purpose, parameters, and return value
  - Lines 51-53: Checks if tenant slug already exists
  - Lines 56-60: Creates a new tenant
  - Lines 61-63: Commits to the database and refreshes the tenant
  - Line 65: Returns the new tenant
- Lines 68-88: Defines the list_tenants endpoint (super admin only)
  - Lines 70-74: Function parameters including pagination, database session, and current user (must be super admin)
  - Lines 75-86: Function docstring explaining purpose, parameters, and return value
  - Line 87: Queries the database for tenants with pagination
  - Line 88: Returns the tenants
- Lines 91-111: Defines the get_tenant endpoint (super admin only)
  - Lines 93-96: Function parameters including tenant ID, database session, and current user (must be super admin)
  - Lines 97-107: Function docstring explaining purpose, parameters, and return value
  - Lines 108-110: Queries the database for the tenant and returns it
- Lines 114-147: Defines the update_tenant endpoint (super admin only)
  - Lines 116-120: Function parameters including tenant ID, tenant data, database session, and current user (must be super admin)
  - Lines 121-132: Function docstring explaining purpose, parameters, and return value
  - Lines 133-135: Queries the database for the tenant
  - Lines 138-141: Updates the tenant fields if provided
  - Lines 143-145: Updates the timestamp, commits to the database, and refreshes the tenant
  - Line 147: Returns the updated tenant
- Lines 150-181: Defines the create_tenant_config endpoint (admin or super admin)
  - Lines 152-156: Function parameters including tenant ID, config data, database session, and current user (must be admin or super admin)
  - Lines 157-168: Function docstring explaining purpose, parameters, and return value
  - Lines 170-172: Checks if tenant exists
  - Lines 175-176: Checks if user is admin of this tenant or super admin
  - Line 179: Sets the tenant config using the service
  - Line 181: Returns the config key and value
- Lines 184-217: Defines the get_tenant_config_value endpoint
  - Lines 186-190: Function parameters including tenant ID, key, database session, and current user
  - Lines 191-202: Function docstring explaining purpose, parameters, and return value
  - Lines 204-206: Checks if tenant exists
  - Lines 209-210: Checks if user belongs to this tenant or is super admin
  - Lines 213-215: Gets the tenant config and checks if it exists
  - Line 217: Returns the config key and value
- Lines 220-258: Defines the list_tenant_configs endpoint
  - Lines 222-225: Function parameters including tenant ID, database session, and current user
  - Lines 226-236: Function docstring explaining purpose, parameters, and return value
  - Lines 238-240: Checks if tenant exists
  - Lines 243-244: Checks if user belongs to this tenant or is super admin
  - Line 247: Queries the database for all tenant configs
  - Lines 249-256: Formats the results, parsing JSON values when possible
  - Line 258: Returns the list of configs

## Schemas Folder <a name="schemas-folder"></a>

The schemas folder contains Pydantic models for request and response validation.

### __init__.py <a name="schemas-init"></a>

**Purpose**: This file initializes the schemas package and exports all schema classes to provide a clean import interface.

**Line-by-Line Description**:
- Lines 0-4: Module docstring explaining the purpose of the file
- Lines 6-12: Imports tenant-related schemas from the tenant module
- Lines 13-23: Imports user-related schemas from the user module
- Lines 24-34: Imports statistics-related schemas from the statistics module
- Lines 36-65: Defines the `__all__` list which specifies all symbols that should be exported when the package is imported with a wildcard import, organized by category (tenant schemas, user schemas, and statistics schemas)

### tenant.py <a name="schemas-tenant"></a>

**Purpose**: This file contains Pydantic schemas for tenant-related data, providing models for request and response validation related to tenant operations.

**Line-by-Line Description**:
- Lines 0-5: Module docstring explaining the purpose of the file
- Line 7: Imports datetime for timestamp handling
- Line 8: Imports typing utilities for type annotations
- Line 9: Imports BaseModel from Pydantic for schema definition
- Line 11: Imports TenantStatus enum from the tenant model
- Lines 14-18: Defines the `TenantCreate` schema for creating a new tenant
  - Line 15: Class docstring explaining the purpose of the schema
  - Line 16: Defines the name field as a required string
  - Line 17: Defines the slug field as a required string
  - Line 18: Defines the status field with a default value of ACTIVE
- Lines 21-24: Defines the `TenantUpdate` schema for updating an existing tenant
  - Line 22: Class docstring explaining the purpose of the schema
  - Line 23: Defines the name field as an optional string
  - Line 24: Defines the status field as an optional TenantStatus enum
- Lines 27-37: Defines the `TenantResponse` schema for tenant response data
  - Line 28: Class docstring explaining the purpose of the schema
  - Line 29: Defines the id field as an integer
  - Line 30: Defines the name field as a string
  - Line 31: Defines the slug field as a string
  - Line 32: Defines the status field as a string
  - Lines 33-34: Defines created_at and updated_at fields as datetime objects
  - Lines 36-37: Configures the schema to work with ORM models
- Lines 40-43: Defines the `TenantConfigCreate` schema for creating a tenant configuration
  - Line 41: Class docstring explaining the purpose of the schema
  - Line 42: Defines the key field as a required string
  - Line 43: Defines the value field as any type
- Lines 46-52: Defines the `TenantConfigResponse` schema for tenant configuration response data
  - Line 47: Class docstring explaining the purpose of the schema
  - Line 48: Defines the key field as a string
  - Line 49: Defines the value field as any type
  - Lines 51-52: Configures the schema to work with ORM models

### user.py <a name="schemas-user"></a>

**Purpose**: This file contains Pydantic schemas for user-related data, providing models for request and response validation related to user operations.

**Line-by-Line Description**:
- Lines 0-5: Module docstring explaining the purpose of the file
- Line 7: Imports datetime for timestamp handling
- Line 8: Imports typing utilities for type annotations
- Line 9: Imports BaseModel, EmailStr, and validator from Pydantic for schema definition and validation
- Line 11: Imports UserRole enum from the user model
- Lines 14-22: Defines the `UserRegister` schema for user registration
  - Line 15: Class docstring explaining the purpose of the schema
  - Line 16: Defines the email field as a required EmailStr
  - Line 17: Defines the password field as a required string
  - Lines 19-22: Defines a validator for the password field, noting that actual validation will be handled in the service layer
- Lines 25-34: Defines the `UserResponse` schema for user response data
  - Line 26: Class docstring explaining the purpose of the schema
  - Line 27: Defines the id field as an integer
  - Line 28: Defines the email field as a string
  - Line 29: Defines the role field as a string
  - Line 30: Defines the tenant_id field as an integer
  - Line 31: Defines the created_at field as a datetime object
  - Lines 33-34: Configures the schema to work with ORM models
- Lines 37-41: Defines the `TokenResponse` schema for authentication token response
  - Line 38: Class docstring explaining the purpose of the schema
  - Line 39: Defines the access_token field as a string
  - Line 40: Defines the refresh_token field as a string
  - Line 41: Defines the token_type field as a string with a default value of "bearer"
- Lines 44-46: Defines the `PasswordResetRequest` schema for password reset request
  - Line 45: Class docstring explaining the purpose of the schema
  - Line 46: Defines the email field as a required EmailStr
- Lines 49-51: Defines the `PasswordResetVerify` schema for password reset token verification
  - Line 50: Class docstring explaining the purpose of the schema
  - Line 51: Defines the token field as a required string
- Lines 54-62: Defines the `PasswordReset` schema for password reset with new password
  - Line 55: Class docstring explaining the purpose of the schema
  - Line 56: Defines the token field as a required string
  - Line 57: Defines the new_password field as a required string
  - Lines 59-62: Defines a validator for the new_password field, noting that actual validation will be handled in the service layer
- Lines 65-67: Defines the `RefreshTokenRequest` schema for refresh token request
  - Line 66: Class docstring explaining the purpose of the schema
  - Line 67: Defines the refresh_token field as a required string
- Lines 70-79: Defines the `UserActivityResponse` schema for user activity response data
  - Line 71: Class docstring explaining the purpose of the schema
  - Line 72: Defines the activity_type field as a string
  - Line 73: Defines the timestamp field as a datetime object
  - Line 74: Defines the ip_address field as an optional string
  - Line 75: Defines the user_agent field as an optional string
  - Line 76: Defines the details field as an optional string
  - Lines 78-79: Configures the schema to work with ORM models
- Lines 82-86: Defines the `UserActivityHistoryResponse` schema for user activity history response
  - Line 83: Class docstring explaining the purpose of the schema
  - Line 84: Defines the user_id field as an integer
  - Line 85: Defines the email field as a string
  - Line 86: Defines the activities field as a list of UserActivityResponse objects

### statistics.py <a name="schemas-statistics"></a>

**Purpose**: This file contains Pydantic schemas for statistics-related data, providing models for request and response validation related to usage statistics and analytics.

**Line-by-Line Description**:
- Lines 0-5: Module docstring explaining the purpose of the file
- Line 7: Imports typing utilities for type annotations
- Line 8: Imports BaseModel from Pydantic for schema definition
- Lines 11-16: Defines the `MonthlyActiveUsersItem` schema for monthly active users statistics item
  - Line 12: Class docstring explaining the purpose of the schema
  - Line 13: Defines the year field as an integer
  - Line 14: Defines the month field as an integer
  - Line 15: Defines the active_users field as an integer
  - Line 16: Defines the updated_at field as a string
- Lines 19-21: Defines the `MonthlyActiveUsersResponse` schema for monthly active users statistics response
  - Line 20: Class docstring explaining the purpose of the schema
  - Line 21: Defines the mau_statistics field as a list of MonthlyActiveUsersItem objects
- Lines 24-31: Defines the `UsageStatisticsItem` schema for usage statistics item
  - Line 25: Class docstring explaining the purpose of the schema
  - Line 26: Defines the year field as an integer
  - Line 27: Defines the month field as an integer
  - Line 28: Defines the day field as an optional integer
  - Line 29: Defines the activity_type field as a string
  - Line 30: Defines the count field as an integer
  - Line 31: Defines the updated_at field as a string
- Lines 34-36: Defines the `UsageStatisticsResponse` schema for usage statistics response
  - Line 35: Class docstring explaining the purpose of the schema
  - Line 36: Defines the usage_statistics field as a list of UsageStatisticsItem objects
- Lines 39-45: Defines the `TenantStatisticsSummary` schema for tenant statistics summary
  - Line 40: Class docstring explaining the purpose of the schema
  - Line 41: Defines the total_tenants field as an integer
  - Line 42: Defines the active_tenants field as an integer
  - Line 43: Defines the trial_tenants field as an integer
  - Line 44: Defines the inactive_tenants field as an integer
  - Line 45: Defines the suspended_tenants field as an integer
- Lines 48-55: Defines the `TenantDetail` schema for tenant detail in statistics
  - Line 49: Class docstring explaining the purpose of the schema
  - Line 50: Defines the id field as an integer
  - Line 51: Defines the name field as a string
  - Line 52: Defines the slug field as a string
  - Line 53: Defines the status field as a string
  - Line 54: Defines the created_at field as a string
  - Line 55: Defines the user_count field as an integer
- Lines 58-61: Defines the `TenantStatisticsResponse` schema for tenant statistics response
  - Line 59: Class docstring explaining the purpose of the schema
  - Line 60: Defines the summary field as a TenantStatisticsSummary object
  - Line 61: Defines the tenants field as a list of TenantDetail objects
- Lines 64-68: Defines the `GlobalMAUItem` schema for global monthly active users item
  - Line 65: Class docstring explaining the purpose of the schema
  - Line 66: Defines the year field as an integer
  - Line 67: Defines the month field as an integer
  - Line 68: Defines the total_active_users field as an integer
- Lines 71-73: Defines the `GlobalMAUResponse` schema for global monthly active users response
  - Line 72: Class docstring explaining the purpose of the schema
  - Line 73: Defines the global_mau_statistics field as a list of GlobalMAUItem objects

## Services Folder <a name="services-folder"></a>

The services folder contains business logic implementation, separated from the route handlers.

### __init__.py <a name="services-init"></a>

**Purpose**: This file initializes the services package and exports all service functions to provide a clean import interface.

**Line-by-Line Description**:
- Lines 0-4: Module docstring explaining the purpose of the file
- Lines 6-11: Imports user service functions from the user_service module
- Lines 12-18: Imports tenant service functions from the tenant_service module
- Lines 19-25: Imports statistics service functions from the stats_service module
- Lines 27-47: Defines the `__all__` list which specifies all symbols that should be exported when the package is imported with a wildcard import, organized by category (user services, tenant services, and statistics services)

### README.md <a name="services-readme"></a>

**Purpose**: This file provides documentation about the services layer, explaining its purpose and how to use the service functions.

**Line-by-Line Description**:
- Line 0: Title of the document
- Line 2: Introduction to the services layer, explaining its purpose and benefits
- Lines 4-12: Description of the user service and its responsibilities
- Lines 14-20: Description of the tenant service and its responsibilities
- Lines 22-29: Description of the statistics service and its responsibilities
- Lines 31-55: Usage example showing how to use services in route handlers, with a code example demonstrating the separation of concerns

### user_service.py <a name="services-user"></a>

**Purpose**: This file contains service functions for user-related operations, implementing the business logic for user management.

**Line-by-Line Description**:
- Lines 0-4: Module docstring explaining the purpose of the file
- Line 6: Imports datetime for timestamp handling
- Line 7: Imports logging for error and activity logging
- Line 8: Imports necessary FastAPI components for exception handling and background tasks
- Line 9: Imports SQLAlchemy Session for database operations
- Line 11: Imports necessary models for user operations
- Line 12: Imports authentication utilities
- Line 13: Imports email utilities for password reset
- Line 14: Imports dependencies for user activity tracking and tenant configuration
- Line 15: Imports application settings
- Line 18: Sets up a logger for this module
- Lines 20-76: Defines the `register_user` function
  - Lines 21-26: Function parameters including database session, user details, and request object
  - Lines 27-42: Function docstring explaining purpose, parameters, return value, and exceptions
  - Lines 44-50: Checks if email already exists in this tenant
  - Lines 53-54: Validates the password against policy
  - Lines 56-64: Hashes the password, creates the user, and commits to the database
  - Lines 67-73: Records the registration activity
  - Line 75: Logs the registration and returns the new user
- Lines 79-147: Defines the `authenticate_user` function
  - Lines 80-85: Function parameters including database session, user credentials, and request object
  - Lines 86-101: Function docstring explaining purpose, parameters, return value, and exceptions
  - Lines 103-113: Verifies the user's credentials (email)
  - Lines 116-121: Verifies the user's password
  - Lines 124-130: Records the login activity
  - Lines 133-137: Generates an access token with expiration
  - Line 140: Creates a refresh token
  - Lines 143-147: Returns the tokens
- Lines 150-228: Defines the `request_password_reset` function
  - Lines 151-156: Function parameters including database session, email, tenant ID, and optional parameters
  - Lines 157-169: Function docstring explaining purpose, parameters, and return value
  - Lines 171-178: Finds the user and returns success even if user doesn't exist (to prevent email enumeration)
  - Lines 180-184: Gets the tenant and checks if it exists
  - Lines 187-189: Generates a reset token with expiration
  - Lines 192-198: Stores the token in the database
  - Lines 201-208: Records the password reset request activity
  - Lines 211-216: Gets tenant-specific frontend URL if configured
  - Lines 219-226: Sends reset email in background if background tasks are available
  - Line 228: Returns success
- Lines 231-300: Defines the `reset_password` function
  - Lines 232-236: Function parameters including database session, token, new password, and request object
  - Lines 237-251: Function docstring explaining purpose, parameters, return value, and exceptions
  - Lines 253-259: Finds the token in the database
  - Lines 262-265: Checks if the token is expired
  - Lines 268-274: Gets user and tenant info and checks if tenant is active
  - Lines 277-278: Validates the new password
  - Lines 280-281: Updates the user's password
  - Lines 283-290: Records the password reset completion activity
  - Lines 293-294: Marks the token as used
  - Lines 296-297: Revokes all refresh tokens for this user
  - Line 298: Commits the changes to the database
  - Line 300: Returns success

### tenant_service.py <a name="services-tenant"></a>

**Purpose**: This file contains service functions for tenant-related operations, implementing the business logic for tenant management.

**Line-by-Line Description**:
- Lines 0-4: Module docstring explaining the purpose of the file
- Line 6: Imports logging for error and activity logging
- Line 7: Imports json for handling JSON configuration values
- Line 8: Imports HTTPException from FastAPI for error handling
- Line 9: Imports SQLAlchemy Session for database operations
- Line 11: Imports necessary models for tenant operations
- Line 14: Sets up a logger for this module
- Lines 16-48: Defines the `create_tenant` function
  - Line 16: Function parameters including database session and tenant details
  - Lines 17-31: Function docstring explaining purpose, parameters, return value, and exceptions
  - Lines 33-35: Checks if tenant slug already exists
  - Lines 38-42: Creates a new tenant
  - Lines 43-45: Commits to the database and refreshes the tenant
  - Line 47: Logs the creation and returns the new tenant
- Lines 50-82: Defines the `update_tenant` function
  - Line 50: Function parameters including database session, tenant ID, and optional parameters
  - Lines 51-65: Function docstring explaining purpose, parameters, return value, and exceptions
  - Lines 66-68: Finds the tenant and checks if it exists
  - Lines 71-74: Updates the tenant fields if provided
  - Lines 76-79: Updates the timestamp, commits to the database, and refreshes the tenant
  - Line 81: Logs the update and returns the updated tenant
- Lines 84-110: Defines the `get_tenant_config` function
  - Line 84: Function parameters including database session, tenant ID, key, and default value
  - Lines 85-96: Function docstring explaining purpose, parameters, and return value
  - Lines 97-100: Queries the database for the configuration
  - Lines 102-103: Returns the default value if configuration is not found
  - Lines 105-110: Tries to parse the value as JSON, returns as string if not valid JSON
- Lines 112-156: Defines the `set_tenant_config` function
  - Line 112: Function parameters including database session, tenant ID, key, and value
  - Lines 113-127: Function docstring explaining purpose, parameters, return value, and exceptions
  - Lines 129-131: Checks if tenant exists
  - Lines 134-135: Converts value to JSON string if it's not a string
  - Lines 137-140: Queries the database for existing configuration
  - Lines 142-152: Updates existing configuration or creates a new one
  - Lines 154-156: Commits to the database, refreshes the configuration, and returns it
- Lines 158-186: Defines the `check_tenant_access` function
  - Line 158: Function parameters including database session, user, tenant ID, and admin_required flag
  - Lines 159-173: Function docstring explaining purpose, parameters, return value, and exceptions
  - Lines 175-176: Super admins have access to all tenants
  - Lines 179-180: Checks if user belongs to this tenant
  - Lines 183-184: Checks if admin access is required
  - Line 186: Returns true if all checks pass

### stats_service.py <a name="services-stats"></a>

**Purpose**: This file contains service functions for statistics and analytics operations, implementing the business logic for data analysis.

**Line-by-Line Description**:
- Lines 0-4: Module docstring explaining the purpose of the file
- Line 6: Imports logging for error and activity logging
- Line 7: Imports datetime for timestamp handling
- Lines 8-9: Imports SQLAlchemy functions for database operations
- Lines 11-18: Imports necessary models for statistics operations
- Line 21: Sets up a logger for this module
- Lines 23-51: Defines the `get_monthly_active_users` function
  - Line 23: Function parameters including database session, tenant ID, and limit
  - Lines 24-34: Function docstring explaining purpose, parameters, and return value
  - Lines 35-40: Queries the database for MAU statistics
  - Lines 42-49: Formats the results
  - Line 51: Returns the formatted statistics
- Lines 53-106: Defines the `get_usage_statistics` function
  - Lines 54-60: Function parameters including database session, tenant ID, and optional filters
  - Lines 61-74: Function docstring explaining purpose, parameters, and return value
  - Line 75: Starts building the query
  - Lines 78-83: Applies filters if provided
  - Lines 86-90: Orders the results by date
  - Line 93: Limits the results and executes the query
  - Lines 95-104: Formats the results
  - Line 106: Returns the formatted statistics
- Lines 108-150: Defines the `get_user_activity_history` function
  - Line 108: Function parameters including database session, user ID, tenant ID, and limit
  - Lines 109-120: Function docstring explaining purpose, parameters, and return value
  - Lines 122-128: Checks if the user exists and belongs to the tenant
  - Lines 131-134: Queries the database for user activities
  - Lines 136-144: Formats the results
  - Lines 146-150: Returns the user activities with user information
- Lines 152-202: Defines the `get_tenant_statistics` function
  - Line 152: Function parameters including database session
  - Lines 153-161: Function docstring explaining purpose, parameters, and return value
  - Lines 163-167: Gets tenant counts by status
  - Lines 170-177: Gets user counts per tenant
  - Lines 180-191: Gets tenant details with user counts
  - Lines 193-201: Returns the tenant statistics summary and details
- Lines 204-249: Defines the `get_global_mau_statistics` function
  - Line 204: Function parameters including database session and optional filters
  - Lines 205-216: Function docstring explaining purpose, parameters, and return value
  - Lines 217-224: Builds the query for global MAU statistics
  - Lines 227-230: Applies filters if provided
  - Lines 233-236: Orders the results by date
  - Line 239: Limits the results and executes the query
  - Lines 241-247: Formats the results
  - Line 249: Returns the formatted statistics

## Utils Folder <a name="utils-folder"></a>

The utils folder contains utility functions and helpers used throughout the application.

### __init__.py <a name="utils-init"></a>

**Purpose**: This file initializes the utils package and exports all utility functions to provide a clean import interface.

**Line-by-Line Description**:
- Lines 0-4: Module docstring explaining the purpose of the file
- Lines 6-20: Imports authentication utilities from the auth module
- Line 21: Imports email utilities from the email module
- Lines 22-28: Imports logging utilities from the logging module
- Lines 29-34: Imports error handling utilities from the error_handling module
- Lines 36-66: Defines the `__all__` list which specifies all symbols that should be exported when the package is imported with a wildcard import, organized by category (authentication utilities, email utilities, logging utilities, and error handling utilities)

### auth.py <a name="utils-auth"></a>

**Purpose**: This file contains authentication utilities for the SaaS platform, providing functions for authentication, token management, and password handling.

**Line-by-Line Description**:
- Lines 0-5: Module docstring explaining the purpose of the file
- Lines 7-16: Imports necessary modules for authentication, including datetime, uuid, jwt, and FastAPI components
- Lines 18-20: Imports application settings, database functions, and models
- Line 23: Sets up a logger for this module
- Line 26: Creates a password hashing context using bcrypt
- Lines 29-34: Defines the password policy with requirements for length, uppercase letters, numbers, and special characters
- Line 37: Creates an OAuth2 scheme for token authentication
- Lines 40-47: Sets up Redis connection for token blacklisting with fallback to in-memory storage
- Lines 50-63: Defines the `blacklist_token` function
  - Lines 51-57: Function docstring explaining purpose and parameters
  - Lines 58-59: Adds token to Redis blacklist if available
  - Lines 61-63: Adds token to in-memory blacklist with expiration time if Redis is not available
- Lines 66-86: Defines the `is_token_blacklisted` function
  - Lines 67-75: Function docstring explaining purpose, parameters, and return value
  - Lines 76-77: Checks if token is in Redis blacklist if available
  - Lines 79-86: Cleans up expired tokens from in-memory blacklist and checks if token is blacklisted
- Lines 89-99: Defines the `cleanup_expired_tokens` function
  - Lines 90-95: Function docstring explaining purpose and parameters
  - Lines 96-99: Deletes expired refresh tokens and password reset tokens from the database
- Lines 102-117: Defines the `create_access_token` function
  - Lines 103-112: Function docstring explaining purpose, parameters, and return value
  - Lines 113-116: Creates a JWT token with expiration time and type
- Lines 120-151: Defines the `create_refresh_token` function
  - Lines 121-130: Function docstring explaining purpose, parameters, and return value
  - Lines 132-133: Generates a unique token with expiration time
  - Lines 136-143: Stores the token in the database
  - Lines 146-151: Creates a JWT token with token ID and returns it
- Lines 154-237: Defines the `verify_token` function
  - Lines 155-169: Function docstring explaining purpose, parameters, return value, and exceptions
  - Lines 171-172: Checks if token is blacklisted
  - Lines 174-179: Decodes the token and verifies its type
  - Lines 182-198: Handles access tokens by extracting user ID and tenant ID, finding the user, and checking if tenant is active
  - Lines 201-232: Handles refresh tokens by extracting user ID and token JTI, verifying the token exists in the database and is not revoked, checking if token is expired, finding the user, and checking if tenant is active
  - Lines 234-237: Handles JWT exceptions
- Lines 240-251: Defines the `get_current_user` dependency function
  - Lines 241-250: Function docstring explaining purpose, parameters, and return value
  - Line 251: Calls verify_token with token type "access"
- Lines 254-280: Defines the `validate_password` function
  - Lines 255-263: Function docstring explaining purpose, parameters, and exceptions
  - Lines 264-280: Tests password against policy and raises HTTPException with detailed error messages if validation fails
- Lines 283-293: Defines the `hash_password` function
  - Lines 284-292: Function docstring explaining purpose, parameters, and return value
  - Line 293: Hashes the password using the password context
- Lines 296-306: Defines the `verify_password` function
  - Lines 297-306: Function docstring explaining purpose, parameters, and return value
  - Line 307: Verifies the password against the hash using the password context

### email.py <a name="utils-email"></a>

**Purpose**: This file contains email utilities for the SaaS platform, providing functions for sending emails, including password reset emails.

**Line-by-Line Description**:
- Lines 0-4: Module docstring explaining the purpose of the file
- Lines 6-9: Imports necessary modules for email handling
- Line 11: Imports application settings
- Line 14: Sets up a logger for this module
- Lines 16-62: Defines the `send_reset_email` function
  - Lines 17-28: Function docstring explaining purpose, parameters, and return value
  - Lines 30-31: Creates the reset link using the frontend URL and token
  - Lines 34-44: Creates the email subject and body
  - Lines 46-50: Creates the email message with sender, recipient, subject, and body
  - Lines 53-56: Sends the email using SMTP
  - Line 58: Logs the successful email sending
  - Lines 60-62: Handles exceptions and logs errors

### logging.py <a name="utils-logging"></a>

**Purpose**: This file contains logging configuration for the SaaS platform, setting up structured logging with request ID correlation.

**Line-by-Line Description**:
- Lines 0-4: Module docstring explaining the purpose of the file
- Lines 6-10: Imports necessary modules for logging
- Lines 12-31: Defines the `RequestIdFilter` class
  - Lines 13-18: Class docstring explaining purpose
  - Lines 20-31: Defines the filter method that adds request_id to log records
- Lines 33-66: Defines the `JsonFormatter` class
  - Lines 34-39: Class docstring explaining purpose
  - Lines 41-66: Defines the format method that formats log records as JSON objects
- Lines 68-99: Defines the `setup_logging` function
  - Lines 69-74: Function docstring explaining purpose and parameters
  - Lines 76-77: Creates and configures the root logger
  - Lines 80-81: Removes existing handlers
  - Lines 84-85: Creates a console handler with JSON formatter
  - Lines 88-89: Adds request ID filter to the handler
  - Line 92: Adds the handler to the root logger
  - Lines 95-98: Configures specific loggers
- Lines 100-110: Defines the `get_logger` function
  - Lines 101-109: Function docstring explaining purpose, parameters, and return value
  - Line 110: Returns a logger with the specified name
- Lines 112-129: Defines the `log_with_request_id` function
  - Lines 113-122: Function docstring explaining purpose and parameters
  - Lines 123-128: Extracts request ID from request if available and logs the message with the request ID

### error_handling.py <a name="utils-error"></a>

**Purpose**: This file contains error handling utilities for the SaaS platform, providing centralized error handling with request ID correlation.

**Line-by-Line Description**:
- Lines 0-4: Module docstring explaining the purpose of the file
- Lines 6-11: Imports necessary modules for error handling
- Line 13: Imports the get_logger function from the logging module
- Line 16: Sets up a logger for this module
- Lines 18-45: Defines the `validation_exception_handler` function
  - Lines 19-28: Function docstring explaining purpose, parameters, and return value
  - Line 29: Extracts request ID from request state
  - Lines 32-35: Logs the error with request ID
  - Lines 38-44: Returns a structured error response with validation details and request ID
- Lines 47-77: Defines the `sqlalchemy_exception_handler` function
  - Lines 48-57: Function docstring explaining purpose, parameters, and return value
  - Line 58: Extracts request ID from request state
  - Lines 61-67: Logs the error with request ID and traceback
  - Lines 70-76: Returns a structured error response with request ID
- Lines 79-109: Defines the `general_exception_handler` function
  - Lines 80-89: Function docstring explaining purpose, parameters, and return value
  - Line 90: Extracts request ID from request state
  - Lines 93-99: Logs the error with request ID and traceback
  - Lines 102-108: Returns a structured error response with request ID
- Lines 111-120: Defines the `setup_error_handlers` function
  - Lines 112-117: Function docstring explaining purpose and parameters
  - Lines 118-120: Adds exception handlers to the FastAPI application

## Conclusion <a name="conclusion"></a>

The SaaS Refactor project demonstrates a well-structured FastAPI application with clear separation of concerns. The codebase is organized into distinct components:

1. **Routes**: Handle HTTP requests and responses, delegating business logic to services
2. **Schemas**: Validate request and response data using Pydantic models
3. **Services**: Implement business logic, separated from HTTP concerns
4. **Utils**: Provide reusable utility functions for authentication, email, logging, and error handling

This architecture promotes maintainability, testability, and scalability. The multi-tenant design allows for efficient resource sharing while maintaining data isolation between tenants. The authentication system provides secure access control with JWT tokens, refresh tokens, and password management. The statistics and analytics features enable monitoring of user activity and tenant usage.

The project follows best practices such as:
- Comprehensive error handling with request ID correlation
- Structured logging with JSON formatting
- Password security with bcrypt hashing and policy enforcement
- Token blacklisting with Redis (with in-memory fallback)
- Clean separation of concerns with dependency injection

This documentation provides a detailed understanding of the codebase structure and functionality, serving as a reference for developers working on the project.
