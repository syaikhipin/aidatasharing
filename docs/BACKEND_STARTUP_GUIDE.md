# Backend Startup Guide

## Overview

The AI Share Platform backend provides two data sharing modes:
1. **Upload Mode**: Traditional file upload and sharing
2. **Connector Mode**: Secure proxy access to external databases and APIs

## Quick Start

### Prerequisites

1. **Environment Setup**
   ```bash
   # Install dependencies
   cd backend
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   - Ensure `.env` file exists in the `backend` directory
   - Key configurations are automatically loaded

### Starting the Backend

#### Method 1: Using the Startup Script (Recommended)

```bash
cd backend
python start.py
```

This will:
- ✅ Load environment variables from `.env` file
- ✅ Validate configuration
- ✅ Initialize the database
- ✅ Start the main API server on port 8000
- ✅ Automatically start the integrated proxy service

#### Method 2: Direct Python Execution

```bash
cd backend
python main.py
```

#### Method 3: Using Uvicorn Directly

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Service Status Verification

### 1. Main Backend Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-21T18:14:15.607042",
  "version": "2.0.0",
  "services": {
    "database": {"status": "connected", "type": "SQLite"},
    "mindsdb": {"status": "available", "url": "http://localhost:47334"},
    "auth_service": {"status": "operational"},
    "file_storage": {"status": "operational"}
  }
}
```

### 2. Integrated Proxy Service Health Check

```bash
curl http://localhost:8000/api/proxy/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "integrated_proxy",
  "timestamp": {
    "enabled": true,
    "running": true,
    "host": "localhost",
    "ports": {
      "mysql": 10101,
      "postgresql": 10102,
      "api": 10103,
      "clickhouse": 10104,
      "mongodb": 10105,
      "s3": 10106,
      "shared": 10107
    }
  }
}
```

### 3. Get Proxy Service Information

```bash
curl http://localhost:8000/api/proxy/info
```

## Available Endpoints

### Main API Endpoints

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Root**: http://localhost:8000/

### Proxy Service Endpoints

#### Management
- **Proxy Health**: `GET http://localhost:8000/api/proxy/health`
- **Proxy Info**: `GET http://localhost:8000/api/proxy/info`
- **Start Proxy**: `POST http://localhost:8000/api/proxy/start`
- **Stop Proxy**: `POST http://localhost:8000/api/proxy/stop`

#### Database Proxies
- **MySQL**: `GET/POST http://localhost:8000/api/proxy/mysql/{database_name}?token={token}`
- **PostgreSQL**: `GET/POST http://localhost:8000/api/proxy/postgresql/{database_name}?token={token}`
- **ClickHouse**: `GET/POST http://localhost:8000/api/proxy/clickhouse/{database_name}?token={token}`
- **MongoDB**: `GET/POST http://localhost:8000/api/proxy/mongodb/{database_name}?token={token}`
- **S3**: `GET/POST http://localhost:8000/api/proxy/s3/{database_name}?token={token}`

#### API Proxies
- **External APIs**: `GET/POST http://localhost:8000/api/proxy/api/{api_name}?token={token}`

#### Shared Links
- **Shared Access**: `GET/POST http://localhost:8000/api/proxy/shared/{share_id}`

## Environment Configuration

Key environment variables in `backend/.env`:

```bash
# Proxy Service Configuration
ENABLE_PROXY_SERVICE=true
PROXY_HOST=localhost

# Proxy Ports (virtual - run within main backend)
PROXY_MYSQL_PORT=10101
PROXY_POSTGRESQL_PORT=10102
PROXY_API_PORT=10103
PROXY_CLICKHOUSE_PORT=10104
PROXY_MONGODB_PORT=10105
PROXY_S3_PORT=10106
PROXY_SHARED_PORT=10107

# Main Server
DATABASE_URL=sqlite:///../storage/aishare_platform.db
GOOGLE_API_KEY=your_google_api_key_here
MINDSDB_URL=http://localhost:47334

# CORS Configuration
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## Demo Accounts

The system comes with pre-configured demo accounts:

- **Admin**: `admin@example.com` / `SuperAdmin123!`
- **TechCorp User**: `alice@techcorp.com` / `Password123!`
- **DataAnalytics User**: `bob@dataanalytics.com` / `Password123!`

## Troubleshooting

### Common Issues

1. **Port 8000 already in use**
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```

2. **Google API Key not found**
   - Check that `GOOGLE_API_KEY` is set in `backend/.env`
   - Restart the backend after updating the .env file

3. **MindsDB connection issues**
   - Ensure MindsDB is running on http://localhost:47334
   - Start MindsDB using: `./start-mindsdb.sh`

4. **Database initialization errors**
   - Check that the `storage` directory exists
   - Ensure proper file permissions

### Logs

- **Backend logs**: Console output when running `python start.py`
- **Background logs**: `logs/backend_test.log` (when started with nohup)

## Development Mode

For development with auto-reload:

```bash
cd backend
python start.py
# or
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Production Deployment

For production deployment, consider:

1. **Use a process manager** (e.g., systemd, supervisor)
2. **Configure proper logging**
3. **Set up reverse proxy** (nginx, Apache)
4. **Use environment-specific configuration**
5. **Enable SSL/TLS**

## Architecture Notes

- **Integrated Design**: Proxy service runs within the main backend process
- **No Separate Processes**: All functionality is unified in a single service
- **Automatic Startup**: Proxy service starts automatically with the backend
- **Shared Configuration**: Uses the same database and configuration as the main API