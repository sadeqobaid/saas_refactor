-- PostgreSQL Database Creation Script for SaaS Platform
-- Generated based on SQLAlchemy models

-- =============================================
-- Database Creation
-- =============================================
CREATE DATABASE saas_platform;

-- Connect to the database
\c saas_platform;

-- =============================================
-- Extensions
-- =============================================
-- Enable UUID extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for password hashing functions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================
-- Schema Creation
-- =============================================
-- Create schema for the application
CREATE SCHEMA IF NOT EXISTS saas_app;

-- Set the search path
SET search_path TO saas_app, public;

-- =============================================
-- Enum Types
-- =============================================

-- Tenant Status Enum
CREATE TYPE tenant_status AS ENUM (
    'active',
    'inactive',
    'suspended',
    'trial'
);

-- User Role Enum
CREATE TYPE user_role AS ENUM (
    'super_admin',
    'admin',
    'basic_user'
);

-- Activity Type Enum
CREATE TYPE activity_type AS ENUM (
    'login',
    'register',
    'password_reset',
    'password_change',
    'token_refresh',
    'api_access',
    'logout'
);

-- =============================================
-- Table Creation
-- =============================================

-- Tenants Table
-- Stores information about each tenant (customer organization)
CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    status tenant_status NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for tenant slug lookups
CREATE INDEX idx_tenant_slug ON tenants(slug);

-- Create partial index for active and trial tenants (most commonly queried)
CREATE INDEX idx_active_tenants ON tenants(id) 
WHERE status = 'active' OR status = 'trial';

-- Tenant Configuration Table
-- Stores tenant-specific configuration settings
CREATE TABLE tenant_configs (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    value TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uix_tenant_config UNIQUE (tenant_id, key)
);

-- Create index for tenant config lookups
CREATE INDEX idx_tenant_config_lookup ON tenant_configs(tenant_id, key);

-- Users Table
-- Stores user information for all tenants
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'basic_user',
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uix_user_email_tenant UNIQUE (email, tenant_id)
);

-- Create indexes for user lookups
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_tenant ON users(tenant_id);
CREATE INDEX idx_user_tenant_role ON users(tenant_id, role);

-- Refresh Tokens Table
-- Stores JWT refresh tokens for authentication
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(255) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for token lookups
CREATE INDEX idx_refresh_token ON refresh_tokens(token);
CREATE INDEX idx_refresh_token_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_token_expires ON refresh_tokens(expires_at);

-- Create partial index for valid tokens
CREATE INDEX idx_valid_refresh_tokens ON refresh_tokens(user_id, expires_at) 
WHERE revoked = FALSE;

-- Password Reset Tokens Table
-- Stores tokens for password reset functionality
CREATE TABLE password_reset_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(255) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for password reset token lookups
CREATE INDEX idx_reset_token ON password_reset_tokens(token);
CREATE INDEX idx_reset_token_user ON password_reset_tokens(user_id);
CREATE INDEX idx_reset_token_expires ON password_reset_tokens(expires_at);

-- Create partial index for unused tokens
CREATE INDEX idx_valid_reset_tokens ON password_reset_tokens(user_id, expires_at) 
WHERE used = FALSE;

-- User Activities Table
-- Tracks user actions for audit and analytics
CREATE TABLE user_activities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    activity_type activity_type NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Add explicit year, month, day columns for indexing
    activity_year INTEGER,
    activity_month INTEGER,
    activity_day INTEGER,
    ip_address VARCHAR(45),
    user_agent TEXT,
    details TEXT
);

-- Create indexes for activity lookups
CREATE INDEX idx_user_activity_user ON user_activities(user_id);
CREATE INDEX idx_user_activity_tenant ON user_activities(tenant_id);
CREATE INDEX idx_user_activity_type ON user_activities(activity_type);
CREATE INDEX idx_user_activity_timestamp ON user_activities(timestamp);

-- Create composite indexes for common queries
CREATE INDEX idx_user_activity_tenant_timestamp ON user_activities(tenant_id, timestamp);
CREATE INDEX idx_user_activity_user_timestamp ON user_activities(user_id, timestamp);
CREATE INDEX idx_user_activity_tenant_type_timestamp ON user_activities(tenant_id, activity_type, timestamp);

-- Create index on the explicit date columns (no functions needed)
CREATE INDEX idx_activity_year_month ON user_activities(activity_year, activity_month);
CREATE INDEX idx_activity_year_month_day ON user_activities(activity_year, activity_month, activity_day);

-- Monthly Active Users Table
-- Stores aggregated monthly active user counts per tenant
CREATE TABLE monthly_active_users (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    active_users_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uix_mau_tenant_year_month UNIQUE (tenant_id, year, month)
);

-- Create indexes for MAU lookups
CREATE INDEX idx_mau_tenant ON monthly_active_users(tenant_id);
CREATE INDEX idx_mau_tenant_year_month ON monthly_active_users(tenant_id, year, month);

-- Usage Summaries Table
-- Stores aggregated usage statistics
CREATE TABLE usage_summaries (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER,
    activity_type activity_type NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uix_usage_tenant_date_activity UNIQUE (tenant_id, year, month, day, activity_type)
);

-- Create indexes for usage summary lookups
CREATE INDEX idx_usage_tenant ON usage_summaries(tenant_id);
CREATE INDEX idx_usage_tenant_date_activity ON usage_summaries(tenant_id, year, month, day, activity_type);
CREATE INDEX idx_usage_tenant_activity ON usage_summaries(tenant_id, activity_type);

-- =============================================
-- Views
-- =============================================

-- Active Tenants View
-- Shows only active and trial tenants
CREATE OR REPLACE VIEW active_tenants AS
SELECT id, name, slug, status, created_at, updated_at
FROM tenants
WHERE status = 'active' OR status = 'trial';

-- User Count By Tenant View
-- Shows the number of users per tenant
CREATE OR REPLACE VIEW user_count_by_tenant AS
SELECT 
    t.id AS tenant_id,
    t.name AS tenant_name,
    t.slug AS tenant_slug,
    t.status AS tenant_status,
    COUNT(u.id) AS user_count
FROM tenants t
LEFT JOIN users u ON t.id = u.tenant_id
GROUP BY t.id, t.name, t.slug, t.status;

-- Active Users View
-- Shows users who have been active in the last 30 days
CREATE OR REPLACE VIEW active_users AS
SELECT DISTINCT
    u.id,
    u.email,
    u.role,
    u.tenant_id,
    t.name AS tenant_name,
    t.slug AS tenant_slug,
    MAX(ua.timestamp) AS last_activity
FROM users u
JOIN tenants t ON u.tenant_id = t.id
JOIN user_activities ua ON u.id = ua.user_id
WHERE ua.timestamp > (CURRENT_TIMESTAMP - INTERVAL '30 days')
GROUP BY u.id, u.email, u.role, u.tenant_id, t.name, t.slug;

-- Recent Activities View
-- Shows recent user activities with user and tenant information
CREATE OR REPLACE VIEW recent_activities AS
SELECT
    ua.id,
    ua.user_id,
    u.email AS user_email,
    ua.tenant_id,
    t.name AS tenant_name,
    t.slug AS tenant_slug,
    ua.activity_type,
    ua.timestamp,
    ua.ip_address,
    ua.user_agent,
    ua.details
FROM user_activities ua
JOIN users u ON ua.user_id = u.id
JOIN tenants t ON ua.tenant_id = t.id
ORDER BY ua.timestamp DESC
LIMIT 1000;

-- =============================================
-- Functions
-- =============================================

-- Function to hash a password
CREATE OR REPLACE FUNCTION hash_password(password TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN crypt(password, gen_salt('bf', 10));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to verify a password against a hash
CREATE OR REPLACE FUNCTION verify_password(password TEXT, hash TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN hash = crypt(password, hash);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to update tenant's updated_at timestamp
CREATE OR REPLACE FUNCTION update_tenant_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update tenant config's updated_at timestamp
CREATE OR REPLACE FUNCTION update_tenant_config_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update MAU's updated_at timestamp
CREATE OR REPLACE FUNCTION update_mau_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update usage summary's updated_at timestamp
CREATE OR REPLACE FUNCTION update_usage_summary_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to extract and set date parts for user activities
CREATE OR REPLACE FUNCTION set_activity_date_parts()
RETURNS TRIGGER AS $$
BEGIN
    NEW.activity_year := EXTRACT(YEAR FROM NEW.timestamp);
    NEW.activity_month := EXTRACT(MONTH FROM NEW.timestamp);
    NEW.activity_day := EXTRACT(DAY FROM NEW.timestamp);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to log user activity
CREATE OR REPLACE FUNCTION log_user_activity(
    p_user_id INTEGER,
    p_tenant_id INTEGER,
    p_activity_type activity_type,
    p_ip_address VARCHAR(45) DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_details TEXT DEFAULT NULL
)
RETURNS VOID AS $$
DECLARE
    activity_timestamp TIMESTAMP WITH TIME ZONE := CURRENT_TIMESTAMP;
BEGIN
    INSERT INTO user_activities (
        user_id,
        tenant_id,
        activity_type,
        timestamp,
        activity_year,
        activity_month,
        activity_day,
        ip_address,
        user_agent,
        details
    ) VALUES (
        p_user_id,
        p_tenant_id,
        p_activity_type,
        activity_timestamp,
        EXTRACT(YEAR FROM activity_timestamp),
        EXTRACT(MONTH FROM activity_timestamp),
        EXTRACT(DAY FROM activity_timestamp),
        p_ip_address,
        p_user_agent,
        p_details
    );
END;
$$ LANGUAGE plpgsql;

-- Function to update monthly active users count
CREATE OR REPLACE FUNCTION update_monthly_active_users(
    p_tenant_id INTEGER,
    p_year INTEGER,
    p_month INTEGER
)
RETURNS VOID AS $$
DECLARE
    active_count INTEGER;
BEGIN
    -- Count distinct users who were active in the specified month
    SELECT COUNT(DISTINCT user_id) INTO active_count
    FROM user_activities
    WHERE tenant_id = p_tenant_id
      AND activity_year = p_year
      AND activity_month = p_month;
    
    -- Insert or update the MAU record
    INSERT INTO monthly_active_users (
        tenant_id,
        year,
        month,
        active_users_count
    ) VALUES (
        p_tenant_id,
        p_year,
        p_month,
        active_count
    )
    ON CONFLICT (tenant_id, year, month)
    DO UPDATE SET
        active_users_count = active_count,
        updated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Function to update usage summary
CREATE OR REPLACE FUNCTION update_usage_summary(
    p_tenant_id INTEGER,
    p_year INTEGER,
    p_month INTEGER,
    p_day INTEGER,
    p_activity_type activity_type
)
RETURNS VOID AS $$
DECLARE
    activity_count INTEGER;
BEGIN
    -- Count activities of the specified type in the specified period
    IF p_day IS NULL THEN
        SELECT COUNT(*) INTO activity_count
        FROM user_activities
        WHERE tenant_id = p_tenant_id
          AND activity_year = p_year
          AND activity_month = p_month
          AND activity_type = p_activity_type;
    ELSE
        SELECT COUNT(*) INTO activity_count
        FROM user_activities
        WHERE tenant_id = p_tenant_id
          AND activity_year = p_year
          AND activity_month = p_month
          AND activity_day = p_day
          AND activity_type = p_activity_type;
    END IF;
    
    -- Insert or update the usage summary record
    INSERT INTO usage_summaries (
        tenant_id,
        year,
        month,
        day,
        activity_type,
        count
    ) VALUES (
        p_tenant_id,
        p_year,
        p_month,
        p_day,
        p_activity_type,
        activity_count
    )
    ON CONFLICT (tenant_id, year, month, day, activity_type)
    DO UPDATE SET
        count = activity_count,
        updated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Triggers
-- =============================================

-- Trigger to update tenant's updated_at timestamp
CREATE TRIGGER update_tenant_timestamp
BEFORE UPDATE ON tenants
FOR EACH ROW
EXECUTE FUNCTION update_tenant_timestamp();

-- Trigger to update tenant config's updated_at timestamp
CREATE TRIGGER update_tenant_config_timestamp
BEFORE UPDATE ON tenant_configs
FOR EACH ROW
EXECUTE FUNCTION update_tenant_config_timestamp();

-- Trigger to update MAU's updated_at timestamp
CREATE TRIGGER update_mau_timestamp
BEFORE UPDATE ON monthly_active_users
FOR EACH ROW
EXECUTE FUNCTION update_mau_timestamp();

-- Trigger to update usage summary's updated_at timestamp
CREATE TRIGGER update_usage_summary_timestamp
BEFORE UPDATE ON usage_summaries
FOR EACH ROW
EXECUTE FUNCTION update_usage_summary_timestamp();

-- Trigger to set date parts before inserting user activity
CREATE TRIGGER set_activity_date_parts_trigger
BEFORE INSERT ON user_activities
FOR EACH ROW
EXECUTE FUNCTION set_activity_date_parts();

-- Trigger to log user activity after insert
CREATE OR REPLACE FUNCTION log_user_activity_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- Update monthly active users for the current month
    PERFORM update_monthly_active_users(
        NEW.tenant_id,
        NEW.activity_year,
        NEW.activity_month
    );
    
    -- Update usage summary for the current day
    PERFORM update_usage_summary(
        NEW.tenant_id,
        NEW.activity_year,
        NEW.activity_month,
        NEW.activity_day,
        NEW.activity_type
    );
    
    -- Update usage summary for the current month (without day)
    PERFORM update_usage_summary(
        NEW.tenant_id,
        NEW.activity_year,
        NEW.activity_month,
        NULL,
        NEW.activity_type
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger
CREATE TRIGGER after_user_activity_insert
AFTER INSERT ON user_activities
FOR EACH ROW
EXECUTE FUNCTION log_user_activity_trigger();

-- =============================================
-- Initial Data
-- =============================================

-- Insert default super admin tenant
INSERT INTO tenants (name, slug, status)
VALUES ('System Admin', 'system-admin', 'active');

-- Insert default tenant
INSERT INTO tenants (name, slug, status)
VALUES ('Default Tenant', 'default', 'active');

-- Insert super admin user (password: Admin@123)
INSERT INTO users (email, password_hash, role, tenant_id)
VALUES (
    'admin@example.com',
    hash_password('Admin@123'),
    'super_admin',
    (SELECT id FROM tenants WHERE slug = 'system-admin')
);

-- Insert default tenant admin (password: Admin@123)
INSERT INTO users (email, password_hash, role, tenant_id)
VALUES (
    'tenant@example.com',
    hash_password('Admin@123'),
    'admin',
    (SELECT id FROM tenants WHERE slug = 'default')
);

-- Insert default tenant configuration
INSERT INTO tenant_configs (tenant_id, key, value)
VALUES (
    (SELECT id FROM tenants WHERE slug = 'default'),
    'frontend_url',
    'http://localhost:8501'
);

-- Log initial activities
SELECT log_user_activity(
    (SELECT id FROM users WHERE email = 'admin@example.com'),
    (SELECT tenant_id FROM users WHERE email = 'admin@example.com'),
    'register',
    '127.0.0.1',
    'Initial Setup',
    'Super admin user created during initial setup'
);

SELECT log_user_activity(
    (SELECT id FROM users WHERE email = 'tenant@example.com'),
    (SELECT tenant_id FROM users WHERE email = 'tenant@example.com'),
    'register',
    '127.0.0.1',
    'Initial Setup',
    'Tenant admin user created during initial setup'
);

-- =============================================
-- Permissions
-- =============================================

-- Create application role
CREATE ROLE saas_app_user;

-- Grant permissions to the role
GRANT USAGE ON SCHEMA saas_app TO saas_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA saas_app TO saas_app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA saas_app TO saas_app_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA saas_app TO saas_app_user;

-- Create application user
CREATE USER saas_app WITH PASSWORD 'saas_app_password';
GRANT saas_app_user TO saas_app;

-- =============================================
-- End of Script
-- =============================================
