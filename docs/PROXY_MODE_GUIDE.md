# Proxy Mode Guide

## Overview

The AI Share Platform's Proxy Mode enables secure data sharing for external databases and APIs without exposing real credentials. This mode complements the traditional Upload Mode by providing connector-based data access.

## Data Sharing Modes

### 1. Upload Mode (Traditional)
- Users upload files (CSV, JSON, Excel, etc.)
- Files are stored locally or in cloud storage
- Data is shared through download links or AI chat interfaces

### 2. Connector Mode (Proxy-based)
- Users create secure connectors to external databases/APIs
- Real credentials are encrypted and hidden
- Data is accessed through proxy endpoints
- Supports real-time data access without data duplication

## How Proxy Mode Works

```
External API/Database ← [Real Credentials] ← Proxy Service ← [Share Token] ← End User
```

1. **Connector Creation**: Admin creates a connector with real database/API credentials
2. **Credential Encryption**: Real credentials are encrypted and stored securely
3. **Proxy Generation**: System generates proxy endpoints that hide real connection details
4. **Share Link Creation**: Shareable links with tokens provide access to specific data
5. **Secure Access**: End users access data through proxy without seeing real credentials

## Setting Up Proxy Connectors

### 1. Create a Database Connector

```bash
curl -X POST "http://localhost:8000/api/proxy-connectors" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name": "Production MySQL DB",
    "connector_type": "database",
    "description": "Production customer database",
    "real_connection_config": {
      "host": "prod-db.company.com",
      "port": 3306,
      "database": "customers",
      "ssl_disabled": false
    },
    "real_credentials": {
      "username": "db_user",
      "password": "secure_password"
    },
    "is_public": false,
    "allowed_operations": ["SELECT"]
  }'
```

### 2. Create an API Connector

```bash
curl -X POST "http://localhost:8000/api/proxy-connectors" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name": "External REST API",
    "connector_type": "api",
    "description": "Third-party REST API",
    "real_connection_config": {
      "base_url": "https://api.external-service.com",
      "endpoint": "/v1/data"
    },
    "real_credentials": {
      "api_key": "sk-1234567890abcdef",
      "auth_header": "Authorization",
      "auth_prefix": "Bearer "
    },
    "is_public": true,
    "allowed_operations": ["GET", "POST"]
  }'
```

### 3. Create a Shared Link

```bash
curl -X POST "http://localhost:8000/api/proxy-connectors/{connector_id}/shared-links" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name": "Customer Data Access",
    "description": "Shared access to customer analytics",
    "is_public": true,
    "expires_in_hours": 24,
    "max_uses": 100
  }'
```

## Using Proxy Endpoints

### Database Queries

#### MySQL Example
```bash
# Simple SELECT query
curl "http://localhost:8000/api/proxy/mysql/Production_MySQL_DB?token=SHARE_TOKEN&query=SELECT%20*%20FROM%20customers%20LIMIT%2010"

# POST with complex query
curl -X POST "http://localhost:8000/api/proxy/mysql/Production_MySQL_DB?token=SHARE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT customer_id, name, email FROM customers WHERE created_at > \"2024-01-01\""
  }'
```

#### PostgreSQL Example
```bash
curl -X POST "http://localhost:8000/api/proxy/postgresql/Analytics_DB?token=SHARE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT COUNT(*) as total_users FROM users WHERE active = true"
  }'
```

### API Requests

#### GET Request
```bash
curl "http://localhost:8000/api/proxy/api/External_REST_API?token=SHARE_TOKEN&endpoint=/users&limit=10"
```

#### POST Request
```bash
curl -X POST "http://localhost:8000/api/proxy/api/External_REST_API?token=SHARE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "POST",
    "endpoint": "/users",
    "data": {
      "name": "John Doe",
      "email": "john@example.com"
    }
  }'
```

### Shared Link Access

```bash
# Access shared data through share ID
curl "http://localhost:8000/api/proxy/shared/abc123def456?query=SELECT%20*%20FROM%20analytics"

# POST request to shared link
curl -X POST "http://localhost:8000/api/proxy/shared/abc123def456" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT revenue, date FROM sales WHERE date >= \"2024-01-01\""
  }'
```

## Supported Database Types

### 1. MySQL
- **Endpoint**: `/api/proxy/mysql/{database_name}`
- **Features**: Full SQL support, SSL configuration
- **Query Format**: Standard MySQL SQL

### 2. PostgreSQL
- **Endpoint**: `/api/proxy/postgresql/{database_name}`
- **Features**: Full SQL support, SSL configuration
- **Query Format**: Standard PostgreSQL SQL

### 3. ClickHouse
- **Endpoint**: `/api/proxy/clickhouse/{database_name}`
- **Features**: Analytics queries, columnar data
- **Query Format**: ClickHouse SQL

### 4. MongoDB
- **Endpoint**: `/api/proxy/mongodb/{database_name}`
- **Features**: Document queries, aggregation
- **Query Format**: MongoDB query syntax

## Response Formats

### Successful Database Query
```json
{
  "status": "success",
  "data": [
    {"id": 1, "name": "John Doe", "email": "john@example.com"},
    {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
  ],
  "columns": ["id", "name", "email"],
  "row_count": 2
}
```

### Successful API Request
```json
{
  "status": "success",
  "data": {
    "users": [...],
    "total": 150
  },
  "status_code": 200,
  "headers": {
    "content-type": "application/json",
    "x-rate-limit": "100"
  }
}
```

### Error Response
```json
{
  "status": "error",
  "error": "Database connection failed: Access denied for user"
}
```

## Security Features

### 1. Credential Encryption
- All real credentials are encrypted using Fernet encryption
- Encryption keys are stored separately from data
- Credentials are only decrypted during actual data access

### 2. Access Control
- Share tokens control access to specific connectors
- Token expiration and usage limits
- IP-based access restrictions (configurable)

### 3. Operation Restrictions
- Configurable allowed operations (SELECT, INSERT, UPDATE, DELETE)
- Query validation and sanitization
- Rate limiting per connector

### 4. Audit Logging
- All proxy access is logged with user details
- Execution time and status tracking
- Failed access attempt monitoring

## Configuration Options

### Environment Variables
```bash
# Enable/disable proxy service
ENABLE_PROXY_SERVICE=true

# Proxy host configuration
PROXY_HOST=localhost

# Connection timeouts
CONNECTOR_TIMEOUT=30

# SSL configuration
DISABLE_SSL_FOR_LOCALHOST=true
SSL_DEVELOPMENT_MODE=true
```

### Connector Configuration
```json
{
  "real_connection_config": {
    "host": "database.example.com",
    "port": 5432,
    "database": "production",
    "ssl_mode": "require",
    "connect_timeout": 30
  },
  "real_credentials": {
    "username": "db_user",
    "password": "secure_password"
  },
  "allowed_operations": ["SELECT", "INSERT"],
  "rate_limits": {
    "requests_per_minute": 60,
    "max_response_size": 10485760
  }
}
```

## Monitoring and Analytics

### 1. Usage Statistics
```bash
curl "http://localhost:8000/api/proxy-connectors/{connector_id}/stats" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 2. Access Logs
```bash
curl "http://localhost:8000/api/proxy-connectors/{connector_id}/access-logs" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. Performance Metrics
- Query execution times
- Success/failure rates
- Data transfer volumes
- Active connection counts

## Best Practices

### 1. Security
- Use read-only database credentials when possible
- Set appropriate token expiration times
- Regularly rotate API keys and database passwords
- Monitor access logs for suspicious activity

### 2. Performance
- Limit query result sizes
- Use appropriate connection timeouts
- Implement caching for frequently accessed data
- Monitor database connection pools

### 3. Maintenance
- Regularly update connector credentials
- Clean up expired shared links
- Archive old access logs
- Monitor disk usage for log files

## Troubleshooting

### Common Issues

1. **"Database/API not found" Error**
   - Verify connector name spelling
   - Check if connector is active
   - Ensure token has access to the connector

2. **"Token required" Error**
   - Add `?token=YOUR_TOKEN` to the URL
   - Or include `Authorization: Bearer YOUR_TOKEN` header

3. **Connection Timeout**
   - Check database/API server availability
   - Verify network connectivity
   - Increase `CONNECTOR_TIMEOUT` if needed

4. **SSL/TLS Issues**
   - For localhost development, ensure `DISABLE_SSL_FOR_LOCALHOST=true`
   - For production, configure proper SSL certificates

### Debug Steps

1. **Check Proxy Service Status**
   ```bash
   curl http://localhost:8000/api/proxy/health
   ```

2. **Verify Connector Configuration**
   ```bash
   curl "http://localhost:8000/api/proxy-connectors" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

3. **Test Direct Database Connection**
   ```bash
   # Test if you can connect to the database directly
   mysql -h hostname -u username -p database_name
   ```

4. **Check Logs**
   ```bash
   tail -f logs/backend_test.log | grep proxy
   ```

## Migration from Separate Proxy Processes

If you were previously using separate proxy processes (start-proxy.sh), you can now:

1. **Stop old proxy processes**
   ```bash
   ./stop-proxy.sh
   pkill -f proxy_server.py
   ```

2. **Update your applications** to use the new endpoints:
   - Old: `http://localhost:10101/database_name`
   - New: `http://localhost:8000/api/proxy/mysql/database_name`

3. **Remove old proxy scripts** (optional)
   - `start-proxy.sh`
   - `stop-proxy.sh`
   - `backend/proxy_server.py`

The new integrated system provides all the same functionality with better reliability and easier management.