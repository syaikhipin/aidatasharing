# AI Share Platform Documentation

## 📖 Documentation Overview

This directory contains comprehensive documentation for the AI Share Platform, covering both traditional file upload sharing and the new integrated proxy-based connector sharing.

## 📚 Available Guides

### 🚀 [Quick Start Guide](./QUICK_START.md)
Get up and running in 3 simple steps. Perfect for first-time users.

**Contents:**
- Prerequisites and installation
- Service startup (backend + proxy)
- Demo accounts and testing
- Basic API usage examples

### 🔧 [Backend Startup Guide](./BACKEND_STARTUP_GUIDE.md)
Detailed instructions for starting and managing the backend services.

**Contents:**
- Multiple startup methods
- Service health verification
- Environment configuration
- Available endpoints
- Troubleshooting

### 🔗 [Proxy Mode Guide](./PROXY_MODE_GUIDE.md)
Complete guide to the integrated proxy connector system for secure data sharing.

**Contents:**
- Proxy mode architecture
- Creating database and API connectors
- Using proxy endpoints
- Security features
- Monitoring and analytics

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   AI Share Platform                     │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────┐ │
│  │   Upload Mode   │    │     Connector Mode          │ │
│  │                 │    │                             │ │
│  │ • File Upload   │    │ • Database Connectors       │ │
│  │ • Local Storage │    │ • API Connectors            │ │
│  │ • Download      │    │ • Encrypted Credentials     │ │
│  │   Links         │    │ • Proxy Endpoints           │ │
│  │ • AI Chat       │    │ • Share Tokens              │ │
│  └─────────────────┘    └─────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│              Integrated Backend Service                 │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ • FastAPI Main Server (Port 8000)                  │ │
│  │ • Integrated Proxy Service                         │ │
│  │ • Database Management                              │ │
│  │ • Authentication & Authorization                   │ │
│  │ • Google Gemini AI Integration                     │ │
│  │ • MindsDB ML Engine                               │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Reference

### Starting Services

```bash
# Quick start (backend only)
cd backend && python start.py

# Full stack
./start-dev.sh

# With custom MindsDB
./start-mindsdb.sh && cd backend && python start.py
```

### Health Checks

```bash
# Main API
curl http://localhost:8000/health

# Proxy service
curl http://localhost:8000/api/proxy/health

# MindsDB
curl http://localhost:47334/api/status
```

### Key Endpoints

| Endpoint | Purpose |
|----------|---------|
| `http://localhost:8000/docs` | API Documentation |
| `http://localhost:8000/api/auth/login` | Authentication |
| `http://localhost:8000/api/datasets` | File Upload Mode |
| `http://localhost:8000/api/proxy-connectors` | Connector Management |
| `http://localhost:8000/api/proxy/*` | Proxy Data Access |

## 🔐 Authentication

All API endpoints (except health checks and public shares) require JWT authentication:

```bash
# 1. Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "SuperAdmin123!"}'

# 2. Use token in subsequent requests
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "http://localhost:8000/api/datasets"
```

## 📊 Data Sharing Comparison

| Feature | Upload Mode | Connector Mode |
|---------|-------------|----------------|
| **Data Storage** | Local/Cloud files | External databases |
| **Data Currency** | Static snapshots | Real-time access |
| **Setup Complexity** | Simple | Moderate |
| **Credential Management** | Not applicable | Encrypted & hidden |
| **Scalability** | Storage limited | Database limited |
| **Use Cases** | Reports, datasets | Live dashboards, APIs |

## 🛠️ Development

### Project Structure

```
simpleaisharing/
├── backend/                 # Main backend service
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration & database
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── main.py             # FastAPI application
│   ├── start.py            # Startup script
│   └── .env                # Environment configuration
├── frontend/               # React frontend (optional)
├── docs/                   # Documentation (this folder)
├── storage/                # Data storage
├── logs/                   # Log files
└── scripts/                # Utility scripts
```

### Adding New Features

1. **Database Models**: Add to `backend/app/models/`
2. **API Endpoints**: Add to `backend/app/api/`
3. **Business Logic**: Add to `backend/app/services/`
4. **Database Migrations**: Use the migration system in `backend/migrations/`

## 🔒 Security Considerations

### For Production Deployment

1. **Environment Variables**
   - Use strong, unique JWT secrets
   - Rotate API keys regularly
   - Use production-grade databases

2. **Network Security**
   - Enable HTTPS/TLS
   - Configure firewalls
   - Use reverse proxy (nginx/Apache)

3. **Database Security**
   - Use read-only credentials when possible
   - Enable connection encryption
   - Monitor access logs

4. **Access Control**
   - Set appropriate token expiration
   - Implement rate limiting
   - Monitor failed authentication attempts

## 📞 Support

### Getting Help

1. **Check Documentation**: Start with the relevant guide above
2. **API Documentation**: Visit http://localhost:8000/docs for interactive API docs
3. **Logs**: Check service logs for error details
4. **Health Checks**: Verify all services are running properly

### Common Issues

- **Port conflicts**: Use `lsof -ti:PORT | xargs kill -9` to free ports
- **Environment issues**: Ensure `.env` file is properly configured
- **Database errors**: Check file permissions and storage directory
- **Authentication problems**: Verify JWT tokens and user credentials

## 🚀 What's Next?

1. **Start with Quick Start**: Follow the [Quick Start Guide](./QUICK_START.md)
2. **Explore Upload Mode**: Create and share traditional datasets
3. **Try Connector Mode**: Set up database and API connectors
4. **Build Applications**: Use the API to build custom interfaces
5. **Scale for Production**: Implement security and performance optimizations

---

**Happy coding! 🎉**