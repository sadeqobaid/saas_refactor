# SaaS Platform Setup and Configuration Guide

This comprehensive guide will walk you through the process of setting up and configuring the SaaS Platform application on your premises. Follow these instructions carefully to ensure a successful deployment.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [PostgreSQL Installation and Configuration](#postgresql-installation-and-configuration)
3. [Redis Installation and Configuration](#redis-installation-and-configuration)
4. [Python Environment Setup](#python-environment-setup)
5. [Application Deployment](#application-deployment)
6. [Environment Variables Configuration](#environment-variables-configuration)
7. [Database Initialization](#database-initialization)
8. [Running the Application](#running-the-application)
9. [Verifying the Installation](#verifying-the-installation)
10. [Troubleshooting](#troubleshooting)

## System Requirements

### Hardware Requirements
- **CPU**: 2+ cores recommended (1 core minimum)
- **RAM**: 4GB+ recommended (2GB minimum)
- **Disk Space**: 10GB+ free space recommended
- **Network**: Internet connection for package installation

### Software Requirements
- **Operating System**: Ubuntu 20.04 LTS or newer (recommended), or any Linux distribution with equivalent packages
- **Python**: Version 3.8 or newer
- **PostgreSQL**: Version 12 or newer
- **Redis**: Version 6 or newer
- **Additional packages**: As detailed in the installation steps

## PostgreSQL Installation and Configuration

### Installing PostgreSQL

#### On Ubuntu/Debian:
```bash
# Update package lists
sudo apt update

# Install PostgreSQL and required extensions
sudo apt install -y postgresql postgresql-contrib

# Verify installation
sudo systemctl status postgresql
```

#### On Red Hat/CentOS/Fedora:
```bash
# Install PostgreSQL repository
sudo dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-8-x86_64/pgdg-redhat-repo-latest.noarch.rpm

# Install PostgreSQL and required extensions
sudo dnf install -y postgresql12-server postgresql12-contrib

# Initialize the database
sudo /usr/pgsql-12/bin/postgresql-12-setup initdb

# Start and enable PostgreSQL service
sudo systemctl enable postgresql-12
sudo systemctl start postgresql-12

# Verify installation
sudo systemctl status postgresql-12
```

### Configuring PostgreSQL

1. **Set PostgreSQL password for postgres user**:
   ```bash
   sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'your_secure_password';"
   ```

2. **Configure PostgreSQL to allow password authentication**:
   ```bash
   sudo nano /etc/postgresql/12/main/pg_hba.conf
   ```
   
   Find the lines that look like this:
   ```
   # IPv4 local connections:
   host    all             all             127.0.0.1/32            ident
   # IPv6 local connections:
   host    all             all             ::1/128                 ident
   ```
   
   Change `ident` to `md5`:
   ```
   # IPv4 local connections:
   host    all             all             127.0.0.1/32            md5
   # IPv6 local connections:
   host    all             all             ::1/128                 md5
   ```

3. **Restart PostgreSQL to apply changes**:
   ```bash
   sudo systemctl restart postgresql
   ```

4. **Create the database for the SaaS platform**:
   ```bash
   sudo -u postgres createdb saas_platform
   ```

## Redis Installation and Configuration

### Installing Redis

#### On Ubuntu/Debian:
```bash
# Update package lists
sudo apt update

# Install Redis
sudo apt install -y redis-server

# Verify installation
sudo systemctl status redis-server
```

#### On Red Hat/CentOS/Fedora:
```bash
# Install Redis
sudo dnf install -y redis

# Start and enable Redis service
sudo systemctl enable redis
sudo systemctl start redis

# Verify installation
sudo systemctl status redis
```

### Configuring Redis

1. **Configure Redis for better performance**:
   ```bash
   sudo nano /etc/redis/redis.conf
   ```
   
   Make the following changes:
   - Set `maxmemory 256mb` (adjust based on your server's available memory)
   - Set `maxmemory-policy allkeys-lru`

2. **Restart Redis to apply changes**:
   ```bash
   sudo systemctl restart redis-server
   ```

## Python Environment Setup

1. **Install Python and required packages**:
   ```bash
   # Update package lists
   sudo apt update
   
   # Install Python and development tools
   sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential libpq-dev
   ```

2. **Create a directory for the application**:
   ```bash
   sudo mkdir -p /opt/saas_platform
   sudo chown $USER:$USER /opt/saas_platform
   ```

3. **Create and activate a virtual environment**:
   ```bash
   cd /opt/saas_platform
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Upgrade pip**:
   ```bash
   pip install --upgrade pip
   ```

## Application Deployment

1. **Copy the application files to the server**:
   - Extract the application files to `/opt/saas_platform/app`
   - Ensure all files have the correct permissions

2. **Install application dependencies**:
   ```bash
   cd /opt/saas_platform
   source venv/bin/activate
   pip install fastapi uvicorn sqlalchemy pydantic python-jose[cryptography] passlib python-multipart redis python-dotenv slowapi email-validator streamlit requests
   ```

## Environment Variables Configuration

1. **Create a `.env` file in the application directory**:
   ```bash
   cd /opt/saas_platform/app
   nano .env
   ```

2. **Add the following configuration to the `.env` file**:
   ```
   DATABASE_URL=postgresql://postgres:your_secure_password@localhost:5432/saas_platform
   REDIS_URL=redis://localhost:6379/0
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   DB_POOL_SIZE=5
   DB_MAX_OVERFLOW=10
   SMTP_SERVER=smtp.example.com
   SMTP_PORT=587
   SMTP_USERNAME=user@example.com
   SMTP_PASSWORD=password
   ```

   Replace the placeholder values with your actual configuration:
   - `your_secure_password`: The PostgreSQL password you set earlier
   - `your-secret-key-here`: A secure random string for JWT token encryption
   - SMTP settings: Your email server details for sending password reset emails

3. **Secure the `.env` file**:
   ```bash
   chmod 600 .env
   ```

## Database Initialization

1. **Run the database initialization script**:
   ```bash
   cd /opt/saas_platform
   source venv/bin/activate
   
   # Connect to PostgreSQL and run the script
   psql -U postgres -h localhost -d saas_platform -f database_script.sql
   ```

   When prompted, enter the PostgreSQL password you set earlier.

2. **Verify database initialization**:
   ```bash
   psql -U postgres -h localhost -d saas_platform -c "SELECT COUNT(*) FROM tenants;"
   ```

   You should see a count of at least 2 tenants if the initialization was successful.

## Running the Application

### Running the Backend API

1. **Create a systemd service file for the API**:
   ```bash
   sudo nano /etc/systemd/system/saas-api.service
   ```

2. **Add the following content to the service file**:
   ```
   [Unit]
   Description=SaaS Platform API
   After=network.target postgresql.service redis-server.service
   
   [Service]
   User=your_username
   Group=your_username
   WorkingDirectory=/opt/saas_platform/app
   Environment="PATH=/opt/saas_platform/venv/bin"
   ExecStart=/opt/saas_platform/venv/bin/python /opt/saas_platform/app/run.py
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

   Replace `your_username` with your actual username.

3. **Enable and start the service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable saas-api
   sudo systemctl start saas-api
   ```

4. **Check the service status**:
   ```bash
   sudo systemctl status saas-api
   ```

### Running the Streamlit Frontend

1. **Create a systemd service file for the frontend**:
   ```bash
   sudo nano /etc/systemd/system/saas-frontend.service
   ```

2. **Add the following content to the service file**:
   ```
   [Unit]
   Description=SaaS Platform Frontend
   After=network.target saas-api.service
   
   [Service]
   User=your_username
   Group=your_username
   WorkingDirectory=/opt/saas_platform/app
   Environment="PATH=/opt/saas_platform/venv/bin"
   ExecStart=/opt/saas_platform/venv/bin/streamlit run /opt/saas_platform/app/streamlit_app.py
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

   Replace `your_username` with your actual username.

3. **Enable and start the service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable saas-frontend
   sudo systemctl start saas-frontend
   ```

4. **Check the service status**:
   ```bash
   sudo systemctl status saas-frontend
   ```

## Verifying the Installation

1. **Check if the API is running**:
   ```bash
   curl http://localhost:8000/health
   ```
   
   You should receive a JSON response indicating the API is healthy.

2. **Access the API documentation**:
   Open a web browser and navigate to `http://localhost:8000/docs`

3. **Access the Streamlit frontend**:
   Open a web browser and navigate to `http://localhost:8501`

4. **Test user login**:
   - Use the demo credentials:
     - Email: `admin@demo.com`
     - Password: `Demo@123`

## Troubleshooting

### Database Connection Issues

**Symptom**: The application fails to connect to the database.

**Solutions**:
1. Verify PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql
   ```

2. Check database connection settings in `.env` file:
   ```bash
   cat /opt/saas_platform/app/.env | grep DATABASE_URL
   ```

3. Ensure the database exists:
   ```bash
   sudo -u postgres psql -c "\l" | grep saas_platform
   ```

4. Test direct connection to the database:
   ```bash
   psql -U postgres -h localhost -d saas_platform -c "SELECT 1;"
   ```

### Redis Connection Issues

**Symptom**: The application fails to connect to Redis.

**Solutions**:
1. Verify Redis is running:
   ```bash
   sudo systemctl status redis-server
   ```

2. Check Redis connection settings in `.env` file:
   ```bash
   cat /opt/saas_platform/app/.env | grep REDIS_URL
   ```

3. Test direct connection to Redis:
   ```bash
   redis-cli ping
   ```

### API Service Not Starting

**Symptom**: The API service fails to start.

**Solutions**:
1. Check service logs:
   ```bash
   sudo journalctl -u saas-api.service
   ```

2. Verify Python virtual environment:
   ```bash
   ls -la /opt/saas_platform/venv/bin/python
   ```

3. Check application file permissions:
   ```bash
   ls -la /opt/saas_platform/app/run.py
   ```

4. Try running the application manually:
   ```bash
   cd /opt/saas_platform
   source venv/bin/activate
   cd app
   python run.py
   ```

### Frontend Service Not Starting

**Symptom**: The Streamlit frontend service fails to start.

**Solutions**:
1. Check service logs:
   ```bash
   sudo journalctl -u saas-frontend.service
   ```

2. Verify Streamlit installation:
   ```bash
   /opt/saas_platform/venv/bin/streamlit --version
   ```

3. Try running Streamlit manually:
   ```bash
   cd /opt/saas_platform
   source venv/bin/activate
   cd app
   streamlit run streamlit_app.py
   ```

### Authentication Issues

**Symptom**: Unable to log in with provided credentials.

**Solutions**:
1. Verify the user exists in the database:
   ```bash
   sudo -u postgres psql -d saas_platform -c "SELECT email FROM users;"
   ```

2. Check if the tenant is active:
   ```bash
   sudo -u postgres psql -d saas_platform -c "SELECT name, status FROM tenants;"
   ```

3. Reset the admin password:
   ```bash
   sudo -u postgres psql -d saas_platform -c "UPDATE users SET password_hash = crypt('Admin@123', gen_salt('bf', 10)) WHERE email = 'admin@demo.com';"
   ```

## Additional Support

If you encounter issues not covered in this guide, please:

1. Check the application logs:
   ```bash
   sudo journalctl -u saas-api.service -n 100
   sudo journalctl -u saas-frontend.service -n 100
   ```

2. Run the validation script:
   ```bash
   cd /opt/saas_platform
   source venv/bin/activate
   cd app
   python validate.py
   ```

3. Contact our support team at support@example.com with the following information:
   - Error messages from the logs
   - Output of the validation script
   - Description of the issue
   - Steps to reproduce the problem
