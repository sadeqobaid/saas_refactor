# SaaS Platform Business Process and Data Flow Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [System Architecture Overview](#system-architecture-overview)
3. [Tenant Management Processes](#tenant-management-processes)
4. [User Management Processes](#user-management-processes)
5. [Authentication Workflows](#authentication-workflows)
6. [Activity Tracking Processes](#activity-tracking-processes)
7. [Reporting and Analytics Processes](#reporting-and-analytics-processes)
8. [Data Flow Diagrams](#data-flow-diagrams)
9. [System Integration Points](#system-integration-points)
10. [Business Rules and Constraints](#business-rules-and-constraints)

## Introduction

This document provides a comprehensive overview of the business processes and data flows within the SaaS Platform. It describes how data moves through the system, the key business processes that drive the application, and how different components interact with each other.

The SaaS Platform is a multi-tenant application designed to provide secure, isolated environments for multiple organizations (tenants) while sharing the same infrastructure. This document will help stakeholders understand the system's operation from both technical and business perspectives.

## System Architecture Overview

The SaaS Platform follows a modern, layered architecture with clear separation of concerns:

### Component Layers

1. **Presentation Layer**
   - Streamlit frontend application
   - FastAPI OpenAPI documentation

2. **API Layer**
   - FastAPI routes and endpoints
   - Request/response handling
   - Authentication middleware

3. **Service Layer**
   - Business logic implementation
   - Cross-cutting concerns

4. **Data Access Layer**
   - SQLAlchemy ORM models
   - Database connection management

5. **Database Layer**
   - PostgreSQL database
   - Redis for token blacklisting and caching

### Key Components

- **FastAPI Backend**: Provides RESTful API endpoints for all system functionality
- **Streamlit Frontend**: Offers a user-friendly interface for interacting with the system
- **PostgreSQL Database**: Stores all application data with tenant isolation
- **Redis**: Manages token blacklisting and provides caching capabilities

## Tenant Management Processes

### Tenant Lifecycle

The tenant lifecycle encompasses the creation, management, and eventual deactivation of tenant organizations within the system.

#### Tenant Creation Process

1. **Process Trigger**: Super admin initiates tenant creation
2. **Process Steps**:
   - Super admin provides tenant details (name, slug, status)
   - System validates tenant information (unique slug, valid status)
   - System creates tenant record in database
   - System creates default tenant configurations
   - System creates initial admin user for the tenant
   - System logs tenant creation activity
3. **Data Flow**:
   - API request → Tenant validation → Database creation → Response
4. **Business Rules**:
   - Tenant slugs must be unique across the system
   - Initial tenant status is typically "trial"
   - Each tenant must have at least one admin user

#### Tenant Status Management Process

1. **Process Trigger**: Super admin updates tenant status
2. **Process Steps**:
   - Super admin selects tenant to update
   - Super admin changes tenant status (active, inactive, suspended, trial)
   - System updates tenant record
   - System logs status change activity
   - If status changed to inactive or suspended, system prevents new logins
3. **Data Flow**:
   - API request → Tenant lookup → Status update → Response
4. **Business Rules**:
   - Only super admins can change tenant status
   - Status changes are logged for audit purposes
   - Users cannot log in to inactive or suspended tenants
   - Active and trial tenants have full system access

#### Tenant Configuration Management Process

1. **Process Trigger**: Admin or super admin updates tenant configuration
2. **Process Steps**:
   - Admin selects configuration key to update
   - Admin provides new configuration value
   - System validates configuration data
   - System updates or creates configuration record
   - System logs configuration change
3. **Data Flow**:
   - API request → Config validation → Database update → Response
4. **Business Rules**:
   - Tenant admins can only modify their own tenant's configurations
   - Super admins can modify any tenant's configurations
   - Configuration keys follow a predefined schema
   - Some configuration values may be JSON objects

## User Management Processes

### User Lifecycle

The user lifecycle encompasses the registration, management, and eventual deactivation of users within the system.

#### User Registration Process

1. **Process Trigger**: User initiates registration or admin creates user
2. **Process Steps**:
   - User/admin provides email and password
   - System validates email uniqueness within tenant
   - System validates password against security policy
   - System hashes password securely
   - System creates user record with appropriate role
   - System logs registration activity
3. **Data Flow**:
   - API request → Validation → Password hashing → Database creation → Response
4. **Business Rules**:
   - Emails must be unique within a tenant
   - Passwords must meet complexity requirements
   - New self-registered users get basic_user role by default
   - Admin-created users can be assigned any role except super_admin

#### User Role Management Process

1. **Process Trigger**: Admin updates user role
2. **Process Steps**:
   - Admin selects user to update
   - Admin assigns new role (admin or basic_user)
   - System validates role change permissions
   - System updates user record
   - System logs role change activity
3. **Data Flow**:
   - API request → Permission check → Database update → Response
4. **Business Rules**:
   - Only admins can change user roles
   - Admins cannot create or assign super_admin role
   - Role changes are logged for audit purposes
   - Users cannot change their own role

#### Bulk User Creation Process

1. **Process Trigger**: Admin initiates bulk user creation
2. **Process Steps**:
   - Admin uploads file with user data or provides list of users
   - System validates all user data (emails, roles)
   - System creates user records with temporary passwords
   - System sends email notifications to new users
   - System logs bulk creation activity
3. **Data Flow**:
   - API request → Batch validation → Database creation → Email notifications → Response
4. **Business Rules**:
   - All emails must be unique within tenant
   - Temporary passwords must be reset on first login
   - Maximum number of users is limited by tenant configuration
   - Bulk operations are atomic (all succeed or all fail)

## Authentication Workflows

### User Authentication Process

1. **Process Trigger**: User attempts to log in
2. **Process Steps**:
   - User provides email and password
   - System identifies tenant from context
   - System verifies tenant is active
   - System looks up user by email within tenant
   - System verifies password hash
   - System generates access and refresh tokens
   - System logs successful login activity
3. **Data Flow**:
   - API request → Tenant verification → User lookup → Password verification → Token generation → Response
4. **Business Rules**:
   - Failed login attempts are rate-limited
   - Access tokens expire after 30 minutes
   - Refresh tokens expire after 7 days
   - Authentication requires active tenant

### Token Refresh Process

1. **Process Trigger**: Client attempts to refresh access token
2. **Process Steps**:
   - Client provides refresh token
   - System verifies token is valid and not revoked
   - System identifies associated user
   - System verifies user's tenant is active
   - System revokes used refresh token
   - System generates new access and refresh tokens
   - System logs token refresh activity
3. **Data Flow**:
   - API request → Token verification → User lookup → Token revocation → New token generation → Response
4. **Business Rules**:
   - Refresh tokens can only be used once
   - Expired tokens are automatically rejected
   - Token refresh requires active tenant
   - Refresh operations are logged for security

### Password Reset Process

1. **Process Trigger**: User requests password reset
2. **Process Steps**:
   - User provides email address
   - System identifies tenant from context
   - System looks up user by email within tenant
   - System generates unique reset token with expiration
   - System sends reset email with token
   - System logs password reset request
   - User receives email and provides token
   - System verifies token validity and expiration
   - User provides new password
   - System validates password complexity
   - System updates user's password hash
   - System revokes all refresh tokens for user
   - System logs password reset completion
3. **Data Flow**:
   - Request API → User lookup → Token generation → Email delivery
   - Verification API → Token validation → Password update → Token revocation → Response
4. **Business Rules**:
   - Reset tokens expire after 10 minutes
   - Reset tokens can only be used once
   - New passwords must meet complexity requirements
   - All existing sessions are invalidated after password reset

### Logout Process

1. **Process Trigger**: User initiates logout
2. **Process Steps**:
   - Client provides access token
   - System adds token to blacklist until expiration
   - System revokes all refresh tokens for user
   - System logs logout activity
3. **Data Flow**:
   - API request → Token blacklisting → Refresh token revocation → Response
4. **Business Rules**:
   - Blacklisted tokens cannot be used for authentication
   - Logout invalidates all sessions across devices
   - Logout operations are logged for security

## Activity Tracking Processes

### User Activity Logging Process

1. **Process Trigger**: User performs significant action
2. **Process Steps**:
   - System captures action details (type, timestamp, IP, user agent)
   - System associates activity with user and tenant
   - System stores activity record in database
3. **Data Flow**:
   - User action → Activity capture → Database storage
4. **Business Rules**:
   - All authentication events are logged
   - API access can be logged based on configuration
   - Activity logs include contextual information
   - Activities are associated with both user and tenant

### Monthly Active Users Calculation Process

1. **Process Trigger**: End of month or first activity of new month
2. **Process Steps**:
   - System identifies previous month period
   - System counts distinct users with activity per tenant
   - System stores MAU records in database
3. **Data Flow**:
   - Trigger → Database query → Aggregation → Storage
4. **Business Rules**:
   - MAU is calculated per tenant
   - Users are counted only once per month regardless of activity frequency
   - MAU calculations are stored for historical reporting
   - Global MAU aggregates across all tenants

### Usage Summary Aggregation Process

1. **Process Trigger**: Scheduled task or on-demand request
2. **Process Steps**:
   - System defines time period for aggregation
   - System counts activities by type, tenant, and time period
   - System stores aggregated data in usage_summaries table
3. **Data Flow**:
   - Trigger → Database query → Aggregation → Storage
4. **Business Rules**:
   - Summaries can be daily or monthly
   - Aggregation is performed by activity type
   - Summaries are stored per tenant
   - Historical summaries are preserved for trend analysis

## Reporting and Analytics Processes

### Tenant Statistics Reporting Process

1. **Process Trigger**: Super admin requests tenant statistics
2. **Process Steps**:
   - System counts tenants by status
   - System counts users per tenant
   - System compiles tenant details with user counts
   - System returns formatted statistics
3. **Data Flow**:
   - API request → Database queries → Data aggregation → Response
4. **Business Rules**:
   - Only super admins can access cross-tenant statistics
   - Tenant counts are broken down by status
   - User counts are associated with each tenant
   - Statistics are generated on-demand for real-time accuracy

### Monthly Active Users Reporting Process

1. **Process Trigger**: Admin requests MAU statistics
2. **Process Steps**:
   - System retrieves MAU records for tenant
   - System formats data for time-series display
   - System returns MAU statistics
3. **Data Flow**:
   - API request → Database query → Data formatting → Response
4. **Business Rules**:
   - Tenant admins can only view their own MAU statistics
   - Super admins can view global MAU statistics
   - MAU data is presented in reverse chronological order
   - Up to 12 months of history is typically displayed

### Usage Statistics Reporting Process

1. **Process Trigger**: Admin requests usage statistics
2. **Process Steps**:
   - System applies any filters (activity type, time period)
   - System retrieves usage summary records
   - System formats data for display
   - System returns usage statistics
3. **Data Flow**:
   - API request → Filter application → Database query → Data formatting → Response
4. **Business Rules**:
   - Tenant admins can only view their own usage statistics
   - Statistics can be filtered by activity type and time period
   - Results are limited to prevent performance issues
   - Data is presented in reverse chronological order

### User Activity History Reporting Process

1. **Process Trigger**: Admin requests user activity history
2. **Process Steps**:
   - System verifies user belongs to admin's tenant
   - System retrieves activity records for user
   - System formats activity data for display
   - System returns user activity history
3. **Data Flow**:
   - API request → Permission check → Database query → Data formatting → Response
4. **Business Rules**:
   - Admins can only view activities for users in their tenant
   - Activity history is limited to recent activities (e.g., last 50)
   - Activities include contextual information (IP, user agent)
   - Data is presented in reverse chronological order

## Data Flow Diagrams

### User Registration Data Flow

```
┌─────────┐     ┌─────────────┐     ┌───────────────┐     ┌─────────────┐
│  Client  │────▶│  API Layer  │────▶│  Service Layer │────▶│  Database   │
└─────────┘     └─────────────┘     └───────────────┘     └─────────────┘
      │                │                    │                    │
      │                │                    │                    │
      │                │                    │                    │
      │                │                    │                    │
      │                │                    │                    │
┌─────▼────┐     ┌─────▼─────┐     ┌───────▼───────┐     ┌─────▼─────┐
│ User Data │────▶│ Validation │────▶│ Password Hash │────▶│ User Record│
└──────────┘     └───────────┘     └───────────────┘     └───────────┘
                                                               │
                                                               │
                                                         ┌─────▼─────┐
                                                         │ Activity Log│
                                                         └───────────┘
```

### Authentication Data Flow

```
┌─────────┐     ┌─────────────┐     ┌───────────────┐     ┌─────────────┐
│  Client  │────▶│  API Layer  │────▶│  Service Layer │────▶│  Database   │
└─────────┘     └─────────────┘     └───────────────┘     └─────────────┘
      │                │                    │                    │
      │                │                    │                    │
      │                │                    │                    │
┌─────▼────┐     ┌─────▼─────┐     ┌───────▼───────┐     ┌─────▼─────┐
│Credentials│────▶│Tenant Check│────▶│Password Verify│────▶│User Lookup │
└──────────┘     └───────────┘     └───────────────┘     └───────────┘
                                           │                    │
                                           │                    │
                                     ┌─────▼─────┐        ┌─────▼─────┐
                                     │Token Generate│      │Activity Log│
                                     └───────────┘        └───────────┘
                                           │
                                           │
                                     ┌─────▼─────┐
                                     │  Response  │
                                     └───────────┘
```

### Tenant Management Data Flow

```
┌──────────┐     ┌─────────────┐     ┌───────────────┐     ┌─────────────┐
│Super Admin│────▶│  API Layer  │────▶│  Service Layer │────▶│  Database   │
└──────────┘     └─────────────┘     └───────────────┘     └─────────────┘
      │                │                    │                    │
      │                │                    │                    │
      │                │                    │                    │
┌─────▼────┐     ┌─────▼─────┐     ┌───────▼───────┐     ┌─────▼─────┐
│Tenant Data│────▶│ Permission │────▶│  Validation   │────▶│Tenant Record│
└──────────┘     │   Check    │     └───────────────┘     └───────────┘
                 └───────────┘                                  │
                                                                │
                                                          ┌─────▼─────┐
                                                          │Config Record│
                                                          └───────────┘
                                                                │
                                                                │
                                                          ┌─────▼─────┐
                                                          │Activity Log│
                                                          └───────────┘
```

### Reporting Data Flow

```
┌─────────┐     ┌─────────────┐     ┌───────────────┐     ┌─────────────┐
│  Admin   │────▶│  API Layer  │────▶│  Service Layer │────▶│  Database   │
└─────────┘     └─────────────┘     └───────────────┘     └─────────────┘
      │                │                    │                    │
      │                │                    │                    │
      │                │                    │                    │
┌─────▼────┐     ┌─────▼─────┐     ┌───────▼───────┐     ┌─────▼─────┐
│Report Req │────▶│ Permission │────▶│  Query Build  │────▶│Data Retrieval│
└──────────┘     │   Check    │     └───────────────┘     └───────────┘
                 └───────────┘                                  │
                                                                │
                                                          ┌─────▼─────┐
                                                          │Aggregation │
                                                          └───────────┘
                                                                │
                                                                │
                                                          ┌─────▼─────┐
                                                          │  Response  │
                                                          └───────────┘
```

## System Integration Points

The SaaS Platform provides several integration points for external systems:

### API Integration

1. **Authentication API**
   - External systems can authenticate users via the token endpoint
   - JWT tokens can be used for subsequent API calls
   - Token refresh mechanism supports long-running integrations

2. **Tenant Management API**
   - Super admin systems can create and manage tenants
   - Tenant configurations can be updated programmatically

3. **Statistics API**
   - External reporting systems can retrieve usage statistics
   - Data can be filtered and aggregated as needed

### Database Integration

1. **Read-Only Reporting Database**
   - A read replica can be configured for external reporting tools
   - Views provide simplified access to commonly needed data

2. **Data Warehouse ETL**
   - Activity data can be extracted for data warehouse loading
   - ETL processes should respect tenant data isolation

### Email Integration

1. **Password Reset Emails**
   - System sends password reset emails via configured SMTP server
   - Email templates can be customized per tenant

2. **Notification Emails**
   - System can send various notification emails
   - Email delivery can be tracked for reporting

## Business Rules and Constraints

### Tenant Rules

1. **Tenant Isolation**
   - Data must be completely isolated between tenants
   - Users can only access data from their own tenant
   - Cross-tenant operations are restricted to super admins

2. **Tenant Status**
   - Active and trial tenants have full system access
   - Inactive and suspended tenants cannot be accessed
   - Status changes must be logged for audit purposes

3. **Tenant Configuration**
   - Each tenant can have custom configuration settings
   - Some configurations have system-defined defaults
   - Configuration changes are restricted to admins

### User Rules

1. **User Authentication**
   - Users must authenticate with email and password
   - Passwords must meet complexity requirements
   - Failed login attempts are rate-limited
   - Sessions expire after defined periods

2. **User Roles**
   - Super admin: System-wide administration
   - Admin: Tenant-level administration
   - Basic user: Regular user functionality
   - Role assignments are restricted based on user's own role

3. **Password Security**
   - Passwords must be at least 8 characters
   - Passwords must include uppercase, lowercase, number, and special character
   - Passwords are stored as bcrypt hashes
   - Password reset invalidates all existing sessions

### Activity Tracking Rules

1. **Activity Logging**
   - All authentication events must be logged
   - Sensitive operations must be logged
   - Logs must include user, tenant, timestamp, and context
   - Logs are used for security monitoring and usage statistics

2. **Usage Statistics**
   - Monthly active users are calculated per tenant
   - Usage summaries aggregate activity by type and period
   - Statistics are used for reporting and billing

### Security Constraints

1. **Token Management**
   - Access tokens expire after 30 minutes
   - Refresh tokens expire after 7 days
   - Tokens are blacklisted on logout
   - Token validation includes tenant status check

2. **API Security**
   - All API endpoints require authentication (except public ones)
   - Rate limiting prevents abuse
   - Permission checks enforce role-based access
   - Request IDs enable request tracing

3. **Data Protection**
   - Sensitive data is never exposed in logs
   - Passwords are securely hashed
   - Database connections use connection pooling
   - Redis connections are secured

### Performance Constraints

1. **Database Performance**
   - Queries use appropriate indexes
   - Large result sets are paginated
   - Long-running operations use background processing
   - Connection pooling manages database connections

2. **API Performance**
   - Response times should be under 200ms (p95)
   - Heavy operations are asynchronous when possible
   - Rate limiting prevents resource exhaustion
   - Caching improves response times for common queries
