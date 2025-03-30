# SaaS Platform Testing Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [Test Environment Setup](#test-environment-setup)
3. [Test Categories](#test-categories)
4. [Database Tests](#database-tests)
5. [API Endpoint Tests](#api-endpoint-tests)
6. [Authentication Tests](#authentication-tests)
7. [Multi-tenancy Tests](#multi-tenancy-tests)
8. [Frontend Tests](#frontend-tests)
9. [Performance Tests](#performance-tests)
10. [Security Tests](#security-tests)
11. [Test Execution Procedures](#test-execution-procedures)
12. [Test Reporting](#test-reporting)

## Introduction

This document provides comprehensive testing procedures for the SaaS Platform application. It includes detailed test cases with real data examples and expected results for each component of the system. The testing approach follows industry best practices to ensure the application's reliability, security, and performance.

### Testing Objectives

1. Verify that all components of the SaaS Platform function as expected
2. Ensure proper data isolation between tenants
3. Validate authentication and authorization mechanisms
4. Test error handling and edge cases
5. Verify system performance under various load conditions
6. Ensure security of sensitive data and operations

### Testing Methodology

The testing methodology follows a hierarchical approach:

1. **Unit Testing**: Testing individual components in isolation
2. **Integration Testing**: Testing interactions between components
3. **System Testing**: Testing the complete application as a whole
4. **Acceptance Testing**: Validating that the system meets business requirements

## Test Environment Setup

### Prerequisites

- PostgreSQL 12+ database server
- Redis 6+ server
- Python 3.8+ with virtual environment
- FastAPI and Streamlit dependencies installed
- Test data generation scripts

### Database Setup

1. Create a dedicated test database:
   ```sql
   CREATE DATABASE saas_platform_test;
   ```

2. Apply the database schema to the test database:
   ```bash
   psql -U postgres -d saas_platform_test -f database_script.sql
   ```

3. Load test data:
   ```bash
   python load_test_data.py
   ```

### Test Configuration

Create a `.env.test` file with the following configuration:

```
DATABASE_URL=postgresql://postgres:password@localhost:5432/saas_platform_test
REDIS_URL=redis://localhost:6379/1
SECRET_KEY=test-secret-key-for-testing-purposes-only
ALGORITHM=HS256
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
SMTP_SERVER=localhost
SMTP_PORT=1025
SMTP_USERNAME=test
SMTP_PASSWORD=test
```

## Test Categories

The testing is divided into the following categories:

1. **Database Tests**: Verify database schema, constraints, and data integrity
2. **API Endpoint Tests**: Test all API endpoints for correct behavior
3. **Authentication Tests**: Verify user authentication and authorization
4. **Multi-tenancy Tests**: Ensure proper tenant isolation and management
5. **Frontend Tests**: Test the Streamlit user interface
6. **Performance Tests**: Evaluate system performance under load
7. **Security Tests**: Identify security vulnerabilities

## Database Tests

### Test Case DB-001: Database Schema Validation

**Objective**: Verify that the database schema matches the expected structure

**Test Steps**:
1. Connect to the test database
2. Query the information schema to get table definitions
3. Compare with expected schema

**Test Data**:
```sql
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'public' 
ORDER BY table_name, ordinal_position;
```

**Expected Results**:
- All expected tables exist: tenants, tenant_configs, users, refresh_tokens, password_reset_tokens, user_activities, monthly_active_users, usage_summaries
- All tables have the correct columns with appropriate data types
- All primary keys, foreign keys, and indexes are properly defined

### Test Case DB-002: Tenant Creation and Constraints

**Objective**: Verify that tenant creation works and constraints are enforced

**Test Steps**:
1. Insert a new tenant record
2. Attempt to insert a duplicate tenant with the same slug
3. Verify tenant status enum constraints

**Test Data**:
```sql
-- Valid tenant
INSERT INTO tenants (name, slug, status) 
VALUES ('Test Tenant', 'test-tenant', 'active');

-- Duplicate slug (should fail)
INSERT INTO tenants (name, slug, status) 
VALUES ('Another Tenant', 'test-tenant', 'active');

-- Invalid status (should fail)
INSERT INTO tenants (name, slug, status) 
VALUES ('Invalid Tenant', 'invalid-tenant', 'invalid-status');
```

**Expected Results**:
- First insert succeeds
- Second insert fails with unique constraint violation
- Third insert fails with enum constraint violation

### Test Case DB-003: User Creation and Password Hashing

**Objective**: Verify that user creation works with proper password hashing

**Test Steps**:
1. Create a new tenant
2. Insert a new user with a hashed password
3. Verify the password hash using the verify_password function

**Test Data**:
```sql
-- Create tenant
INSERT INTO tenants (name, slug, status) 
VALUES ('User Test Tenant', 'user-test', 'active') 
RETURNING id;

-- Create user with hashed password
INSERT INTO users (email, password_hash, role, tenant_id) 
VALUES ('test@example.com', hash_password('Test@123'), 'admin', 
        (SELECT id FROM tenants WHERE slug = 'user-test'));

-- Verify password
SELECT verify_password('Test@123', password_hash) 
FROM users 
WHERE email = 'test@example.com';
```

**Expected Results**:
- User is created successfully
- Password verification returns true
- Password is stored as a hash, not plaintext

### Test Case DB-004: Foreign Key Constraints

**Objective**: Verify that foreign key constraints are enforced

**Test Steps**:
1. Attempt to create a user with a non-existent tenant_id
2. Attempt to create a tenant_config with a non-existent tenant_id
3. Delete a tenant and verify cascade deletion of related records

**Test Data**:
```sql
-- Invalid tenant_id (should fail)
INSERT INTO users (email, password_hash, role, tenant_id) 
VALUES ('invalid@example.com', hash_password('Test@123'), 'admin', 9999);

-- Invalid tenant_id for config (should fail)
INSERT INTO tenant_configs (tenant_id, key, value) 
VALUES (9999, 'test_key', 'test_value');

-- Create tenant and related records, then delete tenant
INSERT INTO tenants (name, slug, status) 
VALUES ('Cascade Test', 'cascade-test', 'active') 
RETURNING id;

INSERT INTO users (email, password_hash, role, tenant_id) 
VALUES ('cascade@example.com', hash_password('Test@123'), 'admin', 
        (SELECT id FROM tenants WHERE slug = 'cascade-test'));

INSERT INTO tenant_configs (tenant_id, key, value) 
VALUES ((SELECT id FROM tenants WHERE slug = 'cascade-test'), 'test_key', 'test_value');

DELETE FROM tenants WHERE slug = 'cascade-test';

-- Verify records are deleted
SELECT * FROM users WHERE email = 'cascade@example.com';
SELECT * FROM tenant_configs WHERE key = 'test_key';
```

**Expected Results**:
- First and second inserts fail with foreign key violations
- After tenant deletion, no related user or config records exist

### Test Case DB-005: Trigger Functions

**Objective**: Verify that database triggers function correctly

**Test Steps**:
1. Create a tenant and user
2. Update the tenant status and verify the updated_at timestamp changes
3. Update the user's password and verify activity logging

**Test Data**:
```sql
-- Create tenant and user
INSERT INTO tenants (name, slug, status) 
VALUES ('Trigger Test', 'trigger-test', 'trial') 
RETURNING id;

INSERT INTO users (email, password_hash, role, tenant_id) 
VALUES ('trigger@example.com', hash_password('Test@123'), 'admin', 
        (SELECT id FROM tenants WHERE slug = 'trigger-test'));

-- Record initial timestamps
SELECT updated_at FROM tenants WHERE slug = 'trigger-test';

-- Wait 1 second
SELECT pg_sleep(1);

-- Update tenant status
UPDATE tenants SET status = 'active' WHERE slug = 'trigger-test';

-- Check updated timestamp
SELECT updated_at FROM tenants WHERE slug = 'trigger-test';

-- Count user activities before password change
SELECT COUNT(*) FROM user_activities 
WHERE user_id = (SELECT id FROM users WHERE email = 'trigger@example.com') 
AND activity_type = 'password_reset';

-- Update user password
UPDATE users SET password_hash = hash_password('NewTest@123') 
WHERE email = 'trigger@example.com';

-- Count user activities after password change
SELECT COUNT(*) FROM user_activities 
WHERE user_id = (SELECT id FROM users WHERE email = 'trigger@example.com') 
AND activity_type = 'password_reset';
```

**Expected Results**:
- The updated_at timestamp changes after tenant update
- A new user activity record is created after password change

## API Endpoint Tests

### Test Case API-001: Health Check Endpoint

**Objective**: Verify that the health check endpoint returns correct status

**Test Steps**:
1. Send a GET request to /health endpoint
2. Verify response status and content

**Test Data**:
```
GET /health
```

**Expected Results**:
- Status code: 200
- Response contains "status": "healthy"
- Response includes database and Redis status

### Test Case API-002: User Registration

**Objective**: Verify that user registration works correctly

**Test Steps**:
1. Send a POST request to /register endpoint with valid user data
2. Send a POST request with an existing email
3. Send a POST request with invalid password

**Test Data**:
```json
// Valid registration
POST /register
X-Tenant-ID: test-tenant
{
  "email": "newuser@example.com",
  "password": "ValidPass@123"
}

// Duplicate email
POST /register
X-Tenant-ID: test-tenant
{
  "email": "newuser@example.com",
  "password": "AnotherPass@123"
}

// Invalid password
POST /register
X-Tenant-ID: test-tenant
{
  "email": "anotheruser@example.com",
  "password": "weak"
}
```

**Expected Results**:
- First request: Status 200, success message
- Second request: Status 400, "Email already registered" error
- Third request: Status 400, password policy error message

### Test Case API-003: User Authentication

**Objective**: Verify that user authentication works correctly

**Test Steps**:
1. Register a new user
2. Authenticate with correct credentials
3. Authenticate with incorrect password
4. Authenticate with non-existent user

**Test Data**:
```json
// Register user
POST /register
X-Tenant-ID: test-tenant
{
  "email": "authtest@example.com",
  "password": "AuthTest@123"
}

// Correct credentials
POST /token
X-Tenant-ID: test-tenant
{
  "username": "authtest@example.com",
  "password": "AuthTest@123"
}

// Incorrect password
POST /token
X-Tenant-ID: test-tenant
{
  "username": "authtest@example.com",
  "password": "WrongPass@123"
}

// Non-existent user
POST /token
X-Tenant-ID: test-tenant
{
  "username": "nonexistent@example.com",
  "password": "SomePass@123"
}
```

**Expected Results**:
- First request: Status 200, success message
- Second request: Status 200, returns access_token and refresh_token
- Third request: Status 401, "Incorrect email or password" error
- Fourth request: Status 401, "Incorrect email or password" error

### Test Case API-004: Token Refresh

**Objective**: Verify that token refresh works correctly

**Test Steps**:
1. Authenticate a user to get tokens
2. Use refresh token to get new access token
3. Use the same refresh token again (should fail)
4. Use an invalid refresh token

**Test Data**:
```json
// Authenticate
POST /token
X-Tenant-ID: test-tenant
{
  "username": "authtest@example.com",
  "password": "AuthTest@123"
}
// Save access_token and refresh_token

// Valid refresh
POST /refresh-token
{
  "refresh_token": "<saved_refresh_token>"
}

// Reuse refresh token (should fail)
POST /refresh-token
{
  "refresh_token": "<saved_refresh_token>"
}

// Invalid refresh token
POST /refresh-token
{
  "refresh_token": "invalid-token-value"
}
```

**Expected Results**:
- First request: Status 200, returns tokens
- Second request: Status 200, returns new tokens
- Third request: Status 401, token revoked error
- Fourth request: Status 401, invalid token error

### Test Case API-005: Tenant Management

**Objective**: Verify that tenant management endpoints work correctly

**Test Steps**:
1. Authenticate as super admin
2. Create a new tenant
3. List all tenants
4. Get tenant details
5. Update tenant status

**Test Data**:
```json
// Authenticate as super admin
POST /token
{
  "username": "admin@example.com",
  "password": "Admin@123"
}
// Save access_token

// Create tenant
POST /tenants
Authorization: Bearer <access_token>
{
  "name": "API Test Tenant",
  "slug": "api-test",
  "status": "trial"
}

// List tenants
GET /tenants
Authorization: Bearer <access_token>

// Get tenant details
GET /tenants/<tenant_id>
Authorization: Bearer <access_token>

// Update tenant
PUT /tenants/<tenant_id>
Authorization: Bearer <access_token>
{
  "status": "active"
}
```

**Expected Results**:
- First request: Status 200, returns tokens
- Second request: Status 200, returns created tenant
- Third request: Status 200, returns list of tenants
- Fourth request: Status 200, returns tenant details
- Fifth request: Status 200, returns updated tenant with status "active"

### Test Case API-006: Tenant Configuration

**Objective**: Verify that tenant configuration endpoints work correctly

**Test Steps**:
1. Authenticate as admin
2. Create/update tenant configuration
3. Get configuration value
4. List all configurations

**Test Data**:
```json
// Authenticate as admin
POST /token
X-Tenant-ID: api-test
{
  "username": "admin@api-test.com",
  "password": "Admin@123"
}
// Save access_token and tenant_id

// Create configuration
POST /tenants/<tenant_id>/config
Authorization: Bearer <access_token>
{
  "key": "max_users",
  "value": "25"
}

// Get configuration
GET /tenants/<tenant_id>/config/max_users
Authorization: Bearer <access_token>

// List configurations
GET /tenants/<tenant_id>/config
Authorization: Bearer <access_token>
```

**Expected Results**:
- First request: Status 200, returns tokens
- Second request: Status 200, returns created config
- Third request: Status 200, returns config with value "25"
- Fourth request: Status 200, returns list of configs including max_users

### Test Case API-007: Statistics Endpoints

**Objective**: Verify that statistics endpoints work correctly

**Test Steps**:
1. Authenticate as admin
2. Get monthly active users statistics
3. Get usage statistics
4. Get user activity history

**Test Data**:
```json
// Authenticate as admin
POST /token
X-Tenant-ID: api-test
{
  "username": "admin@api-test.com",
  "password": "Admin@123"
}
// Save access_token, user_id

// Get MAU statistics
GET /admin/stats/mau
Authorization: Bearer <access_token>

// Get usage statistics
GET /admin/stats/usage
Authorization: Bearer <access_token>

// Get user activity
GET /admin/stats/user-activity/<user_id>
Authorization: Bearer <access_token>
```

**Expected Results**:
- First request: Status 200, returns tokens
- Second request: Status 200, returns MAU statistics
- Third request: Status 200, returns usage statistics
- Fourth request: Status 200, returns user activity history

## Authentication Tests

### Test Case AUTH-001: Password Validation

**Objective**: Verify that password validation enforces security policies

**Test Steps**:
1. Test various passwords against the password validation function
2. Verify that each password is correctly validated or rejected

**Test Data**:
```
// Too short
"Pass@1"

// No uppercase
"password@123"

// No lowercase
"PASSWORD@123"

// No number
"Password@abc"

// No special character
"Password123"

// Valid password
"ValidPass@123"
```

**Expected Results**:
- First password: Rejected (too short)
- Second password: Rejected (no uppercase)
- Third password: Rejected (no lowercase)
- Fourth password: Rejected (no number)
- Fifth password: Rejected (no special character)
- Sixth password: Accepted

### Test Case AUTH-002: Token Blacklisting

**Objective**: Verify that token blacklisting prevents reuse of logged-out tokens

**Test Steps**:
1. Authenticate a user to get a token
2. Use the token to access a protected endpoint
3. Logout to blacklist the token
4. Attempt to use the same token again

**Test Data**:
```json
// Authenticate
POST /token
X-Tenant-ID: test-tenant
{
  "username": "blacklist@example.com",
  "password": "Test@123"
}
// Save access_token

// Access protected endpoint
GET /
Authorization: Bearer <access_token>

// Logout
POST /logout
Authorization: Bearer <access_token>

// Try to access protected endpoint again
GET /
Authorization: Bearer <access_token>
```

**Expected Results**:
- First request: Status 200, returns tokens
- Second request: Status 200, returns welcome message
- Third request: Status 200, logout success
- Fourth request: Status 401, token revoked error

### Test Case AUTH-003: Password Reset Flow

**Objective**: Verify the complete password reset flow

**Test Steps**:
1. Request password reset for a user
2. Verify the reset token
3. Reset the password with the token
4. Authenticate with the new password

**Test Data**:
```json
// Request reset
POST /reset-password/request
X-Tenant-ID: test-tenant
{
  "email": "reset@example.com"
}
// Get token from database for testing

// Verify token
POST /reset-password/verify
{
  "token": "<reset_token>"
}

// Reset password
POST /reset-password/reset
{
  "token": "<reset_token>",
  "new_password": "NewPass@123"
}

// Login with new password
POST /token
X-Tenant-ID: test-tenant
{
  "username": "reset@example.com",
  "password": "NewPass@123"
}
```

**Expected Results**:
- First request: Status 200, success message
- Second request: Status 200, token valid message
- Third request: Status 200, password reset success
- Fourth request: Status 200, returns tokens

### Test Case AUTH-004: Role-Based Access Control

**Objective**: Verify that role-based access control works correctly

**Test Steps**:
1. Authenticate as basic user, admin, and super admin
2. Attempt to access endpoints with different permission requirements

**Test Data**:
```json
// Authenticate as basic user
POST /token
X-Tenant-ID: test-tenant
{
  "username": "basic@example.com",
  "password": "Basic@123"
}
// Save basic_token

// Authenticate as admin
POST /token
X-Tenant-ID: test-tenant
{
  "username": "admin@example.com",
  "password": "Admin@123"
}
// Save admin_token

// Authenticate as super admin
POST /token
{
  "username": "superadmin@example.com",
  "password": "Super@123"
}
// Save super_token

// Basic user accessing stats (should fail)
GET /admin/stats/mau
Authorization: Bearer <basic_token>

// Admin accessing stats (should succeed)
GET /admin/stats/mau
Authorization: Bearer <admin_token>

// Admin accessing tenant list (should fail)
GET /tenants
Authorization: Bearer <admin_token>

// Super admin accessing tenant list (should succeed)
GET /tenants
Authorization: Bearer <super_token>
```

**Expected Results**:
- First three requests: Status 200, returns tokens
- Fourth request: Status 403, access forbidden
- Fifth request: Status 200, returns MAU statistics
- Sixth request: Status 403, access forbidden
- Seventh request: Status 200, returns tenant list

## Multi-tenancy Tests

### Test Case MT-001: Tenant Data Isolation

**Objective**: Verify that data is properly isolated between tenants

**Test Steps**:
1. Create two tenants with users in each
2. Authenticate as a user from each tenant
3. Attempt to access data from the other tenant

**Test Data**:
```json
// Create tenants and users in setup

// Authenticate as Tenant A user
POST /token
X-Tenant-ID: tenant-a
{
  "username": "user@tenant-a.com",
  "password": "Test@123"
}
// Save token_a

// Authenticate as Tenant B user
POST /token
X-Tenant-ID: tenant-b
{
  "username": "user@tenant-b.com",
  "password": "Test@123"
}
// Save token_b

// Tenant A user accessing Tenant B config
GET /tenants/<tenant_b_id>/config
Authorization: Bearer <token_a>

// Tenant B user accessing Tenant A config
GET /tenants/<tenant_a_id>/config
Authorization: Bearer <token_b>
```

**Expected Results**:
- First two requests: Status 200, returns tokens
- Third and fourth requests: Status 403, access forbidden

### Test Case MT-002: Tenant Status Management

**Objective**: Verify that tenant status affects user access

**Test Steps**:
1. Create a tenant and user
2. Authenticate as the user
3. Change tenant status to inactive
4. Attempt to authenticate again

**Test Data**:
```json
// Create tenant and user in setup

// Authenticate as user
POST /token
X-Tenant-ID: status-test
{
  "username": "user@status-test.com",
  "password": "Test@123"
}
// Save token

// Access protected endpoint
GET /
Authorization: Bearer <token>

// Update tenant status to inactive (as super admin)
PUT /tenants/<tenant_id>
Authorization: Bearer <super_admin_token>
{
  "status": "inactive"
}

// Try to authenticate again
POST /token
X-Tenant-ID: status-test
{
  "username": "user@status-test.com",
  "password": "Test@123"
}

// Try to use existing token
GET /
Authorization: Bearer <token>
```

**Expected Results**:
- First request: Status 200, returns tokens
- Second request: Status 200, returns welcome message
- Third request: Status 200, returns updated tenant
- Fourth request: Status 403, tenant not active error
- Fifth request: Status 403, tenant not active error

## Frontend Tests

### Test Case FE-001: User Registration Form

**Objective**: Verify that the Streamlit registration form works correctly

**Test Steps**:
1. Navigate to the registration page
2. Submit the form with valid data
3. Submit the form with an existing email
4. Submit the form with an invalid password

**Test Data**:
```
// Valid registration
Email: frontend@example.com
Password: Frontend@123

// Duplicate email
Email: frontend@example.com
Password: Another@123

// Invalid password
Email: another@example.com
Password: weak
```

**Expected Results**:
- First submission: Success message displayed
- Second submission: Error message about duplicate email
- Third submission: Password policy error message displayed

### Test Case FE-002: User Login Form

**Objective**: Verify that the Streamlit login form works correctly

**Test Steps**:
1. Navigate to the login page
2. Submit the form with valid credentials
3. Submit the form with incorrect password
4. Submit the form with non-existent user

**Test Data**:
```
// Valid login
Email: frontend@example.com
Password: Frontend@123

// Incorrect password
Email: frontend@example.com
Password: WrongPass@123

// Non-existent user
Email: nonexistent@example.com
Password: SomePass@123
```

**Expected Results**:
- First submission: Redirected to dashboard
- Second submission: Error message about incorrect credentials
- Third submission: Error message about incorrect credentials

### Test Case FE-003: Password Reset Flow

**Objective**: Verify that the Streamlit password reset flow works correctly

**Test Steps**:
1. Navigate to the reset password page
2. Request a reset for a valid email
3. Verify the reset token
4. Set a new password

**Test Data**:
```
// Request reset
Email: reset@example.com

// Verify token (get from database for testing)
Token: <reset_token>

// Reset password
Token: <reset_token>
New Password: NewFrontend@123
Confirm Password: NewFrontend@123
```

**Expected Results**:
- First submission: Success message displayed
- Second submission: Token valid message displayed
- Third submission: Password reset success message displayed

### Test Case FE-004: Dashboard Access

**Objective**: Verify that the dashboard is only accessible when logged in

**Test Steps**:
1. Attempt to access dashboard without logging in
2. Log in with valid credentials
3. Access dashboard
4. Log out
5. Attempt to access dashboard again

**Test Data**:
```
// Login credentials
Email: dashboard@example.com
Password: Dashboard@123
```

**Expected Results**:
- First attempt: Redirected to login page
- After login: Dashboard displayed with welcome message
- After logout: Redirected to login page

## Performance Tests

### Test Case PERF-001: API Response Time

**Objective**: Verify that API endpoints respond within acceptable time limits

**Test Steps**:
1. Measure response time for key API endpoints
2. Verify that response times are within acceptable limits

**Test Data**:
```
GET /health
GET /tenants (with authentication)
POST /token (authentication)
GET /admin/stats/mau (with authentication)
```

**Expected Results**:
- All endpoints respond in under 200ms (p95)
- No endpoint exceeds 500ms response time

### Test Case PERF-002: Database Query Performance

**Objective**: Verify that database queries perform efficiently

**Test Steps**:
1. Execute key database queries with EXPLAIN ANALYZE
2. Verify that query plans use indexes appropriately

**Test Data**:
```sql
EXPLAIN ANALYZE SELECT * FROM users WHERE tenant_id = 1 AND email = 'test@example.com';
EXPLAIN ANALYZE SELECT * FROM user_activities WHERE tenant_id = 1 ORDER BY timestamp DESC LIMIT 100;
EXPLAIN ANALYZE SELECT * FROM tenants WHERE slug = 'test-tenant';
```

**Expected Results**:
- Queries use appropriate indexes
- No sequential scans on large tables
- Query execution time is within acceptable limits

### Test Case PERF-003: Concurrent User Load

**Objective**: Verify system performance under concurrent user load

**Test Steps**:
1. Simulate multiple concurrent users authenticating and accessing endpoints
2. Monitor system resource usage and response times

**Test Data**:
```
Simulate 50 concurrent users:
- 20 users authenticating
- 15 users accessing dashboard
- 10 users viewing statistics
- 5 users managing tenants
```

**Expected Results**:
- System maintains response times under 500ms (p95)
- No errors or timeouts occur
- CPU and memory usage remain within acceptable limits

## Security Tests

### Test Case SEC-001: Password Storage

**Objective**: Verify that passwords are securely stored

**Test Steps**:
1. Register a new user
2. Examine the password hash in the database
3. Verify that the hash is not reversible

**Test Data**:
```json
// Register user
POST /register
X-Tenant-ID: test-tenant
{
  "email": "security@example.com",
  "password": "Security@123"
}

// Query database
SELECT password_hash FROM users WHERE email = 'security@example.com';
```

**Expected Results**:
- Password is stored as a bcrypt hash
- Hash starts with "$2b$" (bcrypt identifier)
- Original password cannot be derived from the hash

### Test Case SEC-002: SQL Injection Prevention

**Objective**: Verify that the application is protected against SQL injection

**Test Steps**:
1. Attempt SQL injection in various input fields
2. Verify that injection attempts are blocked

**Test Data**:
```
// Email field
Email: "admin@example.com' OR 1=1--"

// Tenant slug
Slug: "test'; DROP TABLE users; --"

// Search parameter
?search=test' UNION SELECT * FROM users--
```

**Expected Results**:
- No SQL errors exposed to the client
- Injection attempts do not succeed
- Application responds with validation errors or 400 status codes

### Test Case SEC-003: Cross-Site Scripting (XSS) Prevention

**Objective**: Verify that the application is protected against XSS attacks

**Test Steps**:
1. Attempt to inject script tags in various input fields
2. Verify that script execution is prevented

**Test Data**:
```
// Name field
Name: "<script>alert('XSS')</script>"

// Email field
Email: "test@example.com<script>alert('XSS')</script>"

// Configuration value
Value: "<img src=x onerror=alert('XSS')>"
```

**Expected Results**:
- Script tags are escaped or removed
- No JavaScript execution occurs
- Application displays the input as plain text or rejects it

### Test Case SEC-004: Authentication Brute Force Protection

**Objective**: Verify that the application is protected against brute force attacks

**Test Steps**:
1. Attempt multiple failed logins for the same user
2. Verify that rate limiting is enforced

**Test Data**:
```json
// Repeated login attempts (10+)
POST /token
X-Tenant-ID: test-tenant
{
  "username": "brute@example.com",
  "password": "WrongPass1"
}
// Change password slightly each time
```

**Expected Results**:
- After multiple failed attempts, requests are rate-limited
- 429 Too Many Requests status code is returned
- Rate limit headers indicate when the limit will reset

## Test Execution Procedures

### Automated Testing

1. **Unit Tests**:
   ```bash
   cd /path/to/project
   pytest tests/unit/
   ```

2. **Integration Tests**:
   ```bash
   cd /path/to/project
   pytest tests/integration/
   ```

3. **API Tests**:
   ```bash
   cd /path/to/project
   pytest tests/api/
   ```

### Manual Testing

1. **Frontend Tests**:
   - Start the Streamlit application
   - Navigate through the application manually
   - Follow the test cases in the Frontend Tests section

2. **Security Tests**:
   - Use tools like OWASP ZAP or Burp Suite
   - Follow the test cases in the Security Tests section

## Test Reporting

### Test Report Format

Test reports should include:

1. Test execution date and time
2. Test environment details
3. Summary of test results (pass/fail counts)
4. Detailed results for each test case
5. Any errors or issues encountered
6. Performance metrics (if applicable)

### Sample Test Report

```
Test Report: SaaS Platform
Date: 2025-03-29
Environment: Test

Summary:
- Total Tests: 25
- Passed: 23
- Failed: 2
- Skipped: 0

Failed Tests:
1. API-007: Statistics Endpoints
   Error: Timeout when accessing usage statistics endpoint
   
2. PERF-003: Concurrent User Load
   Error: Response time exceeded threshold (650ms > 500ms)

Performance Metrics:
- Average Response Time: 120ms
- 95th Percentile Response Time: 350ms
- Max Database Connections: 15
- Average CPU Usage: 45%
```

### Continuous Integration

The test suite should be integrated with a CI/CD pipeline to ensure that tests are run automatically on code changes. The pipeline should:

1. Set up the test environment
2. Run the automated tests
3. Generate test reports
4. Notify developers of test failures

## Conclusion

This testing documentation provides a comprehensive approach to testing the SaaS Platform application. By following these test cases and procedures, you can ensure that the application functions correctly, performs well, and is secure against common threats.

Regular testing should be performed as part of the development process, and the test suite should be updated as new features are added or existing features are modified.
