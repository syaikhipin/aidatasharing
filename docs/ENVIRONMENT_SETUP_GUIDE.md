# Environment Configuration Setup Guide

## Overview
The AI Share Platform uses environment variables for configuration management. This guide explains how to set up and manage these configuration files.

## Environment Files

### Backend Environment (`.env`)
Location: `/backend/.env`

This file contains all configuration needed for the backend server. It includes:
- **Security settings** (JWT secrets, passwords)
- **Database configuration** (SQLite by default)
- **AI API keys** (Google Gemini, OpenAI, etc.)
- **Storage settings** (file upload paths, limits)
- **Feature toggles** (AI chat, data sharing)

### Root Environment (`.env`)
Location: `/.env`

This file is used by root-level scripts and contains similar configuration with paths adjusted for root directory execution.

## Quick Setup

### 1. For Development (Already Done)
The development environment is already configured with default values:

```bash
# Backend has been configured with:
backend/.env         # ✅ Created with development defaults
backend/.env.template # ✅ Created as template for customization
```

### 2. Customization
To customize the configuration:

```bash
# Edit the backend environment file
nano backend/.env

# Or copy from template and modify
cp backend/.env.template backend/.env
```

### 3. Verification
Test your configuration:

```bash
# Validate configuration
cd backend
python -m app.core.config_validator

# Start with validation
python start_server.py
```

## Key Configuration Sections

### 🔐 Security (Required)
```bash
JWT_SECRET_KEY=your_secure_jwt_secret_key_here  # At least 32 chars
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=your_secure_password
```

### 🤖 AI Integration
```bash
GOOGLE_API_KEY=your_google_api_key_here  # For Gemini AI
# OPENAI_API_KEY=your_openai_key         # Optional
# ANTHROPIC_API_KEY=your_anthropic_key   # Optional
```

### 📊 Database
```bash
DATABASE_URL=sqlite:///../storage/aishare_platform.db  # SQLite default
```

### 📁 Storage
```bash
STORAGE_BASE_PATH=../storage
UPLOAD_PATH=../storage/uploads
MAX_FILE_SIZE_MB=100
```

### 🌐 Server
```bash
NODE_ENV=development
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## Environment Variables Reference

### Required Variables
- `JWT_SECRET_KEY` - JWT token signing secret (minimum 32 characters)
- `DATABASE_URL` - Database connection string
- `FIRST_SUPERUSER` - Initial admin user email
- `FIRST_SUPERUSER_PASSWORD` - Initial admin password

### Recommended Variables
- `GOOGLE_API_KEY` - Google Gemini API key for AI features
- `NODE_ENV` - Environment type (development/production)
- `BACKEND_CORS_ORIGINS` - Allowed frontend origins

### Optional Variables
- `OPENAI_API_KEY` - OpenAI API integration
- `ANTHROPIC_API_KEY` - Anthropic Claude integration
- `AWS_ACCESS_KEY_ID` - AWS S3 storage
- `AWS_SECRET_ACCESS_KEY` - AWS S3 credentials
- `S3_BUCKET_NAME` - S3 bucket for file storage

## Configuration Validation

The platform includes automatic configuration validation that checks:

### ✅ Validation Checks
- **Environment file existence** and readability
- **Required variables** are set and valid
- **Port conflicts** in service configuration
- **Storage paths** are writable
- **API keys** format validation
- **Database connectivity** setup
- **Security settings** adequacy

### 🛠️ Running Validation
```bash
# Manual validation
cd backend
python -m app.core.config_validator

# Automatic validation (on server start)
python start_server.py
```

### 📋 Validation Output
The validator provides detailed reports:
```
================================================================================
🔍 CONFIGURATION VALIDATION REPORT
================================================================================

✅ VALIDATION PASSED (20):
   • ✅ Environment variables loaded from .env
   • ✅ Required variable JWT_SECRET_KEY is set
   • ✅ Database configuration validated
   ... (detailed status for each check)

================================================================================
✅ CONFIGURATION VALIDATION PASSED
All configuration checks passed successfully.
================================================================================
```

## Troubleshooting

### Common Issues

#### 1. "Environment file not found"
```bash
# Solution: Copy template
cp backend/.env.template backend/.env
```

#### 2. "JWT_SECRET_KEY not set"
```bash
# Solution: Add to .env file
echo "JWT_SECRET_KEY=your_32_character_secret_key_here" >> backend/.env
```

#### 3. "Database path not writable"
```bash
# Solution: Create storage directory
mkdir -p storage
chmod 755 storage
```

#### 4. "Port conflicts detected"
```bash
# Solution: Check port configuration
cd backend
python -c "from app.core.app_config import get_app_config; print(get_app_config().get_all_ports())"
```

### Getting Help

1. **Validation Report**: Run `python -m app.core.config_validator` for detailed status
2. **Configuration Test**: Use `python start_server.py` to test complete startup
3. **Log Files**: Check console output for specific error messages
4. **Template File**: Reference `backend/.env.template` for all available options

## Security Notes

### 🔒 Production Deployment
For production deployment:

1. **Change default passwords**:
   ```bash
   FIRST_SUPERUSER_PASSWORD=strong_production_password
   JWT_SECRET_KEY=cryptographically_secure_random_secret
   ```

2. **Set production environment**:
   ```bash
   NODE_ENV=production
   DEBUG=false
   FORCE_SSL_IN_PRODUCTION=true
   ```

3. **Configure proper CORS**:
   ```bash
   BACKEND_CORS_ORIGINS=https://yourdomain.com
   ```

### 🛡️ Security Best Practices
- Never commit `.env` files to version control
- Use environment-specific configuration files
- Rotate API keys and secrets regularly
- Use strong, unique passwords for admin accounts
- Enable SSL/TLS in production environments

## Integration with Admin Panel

The platform includes an admin panel for environment management:

1. **Access**: Login as admin → Settings → Environment Variables
2. **Real-time editing**: Modify variables through web interface
3. **Automatic reload**: Changes applied without server restart
4. **Backup**: Automatic backup of previous configurations

This provides a user-friendly way to manage configuration without direct file editing.