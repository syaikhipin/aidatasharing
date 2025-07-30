# AI Share Platform - Quick Start Guide

## 🚀 Service Management

### Complete Development Environment
```bash
# Start all services (MindsDB + Backend + Frontend)
./start-dev.sh

# Stop all services
./stop_dev.sh
```

### Individual Services

#### MindsDB Server
```bash
# Start MindsDB only
./start-mindsdb.sh

# Check MindsDB status
curl http://localhost:47334/api/status
```

#### Proxy Services
```bash
# Start proxy services only (requires MindsDB + Backend)
./start-proxy.sh

# Stop proxy services only
./stop-proxy.sh

# Test proxy health
curl http://localhost:10101/health  # MySQL proxy
curl http://localhost:10102/health  # PostgreSQL proxy
```

## 🔧 Setup & Installation

### Initial Setup
```bash
# 1. Create conda environment
./create-conda-env.sh

# 2. Install dependencies
./install-deps.sh

# 3. Install MindsDB
./install-mindsdb.sh

# 4. Setup Google API key (optional)
./setup-google-api-key.sh
```

### Development Workflow
```bash
# 1. Start development environment
./start-dev.sh

# 2. Access services:
#    - Frontend: http://localhost:3000
#    - Backend API: http://localhost:8000
#    - MindsDB: http://localhost:47334

# 3. Stop when done
./stop_dev.sh
```

## 🌐 Service Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Backend API | 8000 | http://localhost:8000 |
| MindsDB | 47334 | http://localhost:47334 |
| MySQL Proxy | 10101 | http://localhost:10101 |
| PostgreSQL Proxy | 10102 | http://localhost:10102 |
| API Proxy | 10103 | http://localhost:10103 |
| ClickHouse Proxy | 10104 | http://localhost:10104 |
| MongoDB Proxy | 10105 | http://localhost:10105 |
| S3 Proxy | 10106 | http://localhost:10106 |
| Shared Links Proxy | 10107 | http://localhost:10107 |

## 📋 Available Scripts

| Script | Purpose |
|--------|---------|
| `start-dev.sh` | Start complete development environment |
| `stop_dev.sh` | Stop complete development environment |
| `start-mindsdb.sh` | Start MindsDB server only |
| `start-proxy.sh` | Start proxy services only |
| `stop-proxy.sh` | Stop proxy services only |
| `install-mindsdb.sh` | Install MindsDB |
| `install-deps.sh` | Install project dependencies |
| `create-conda-env.sh` | Create conda environment |
| `setup-google-api-key.sh` | Configure Google API key |

## 🔍 Troubleshooting

### Check Service Status
```bash
# Check if services are running
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :47334 # MindsDB

# Check proxy services
for port in {10101..10107}; do
  curl -s http://localhost:$port/health && echo " - Port $port: OK"
done
```

### View Logs
```bash
# Development logs
tail -f logs/backend.log
tail -f logs/frontend.log
tail -f logs/mindsdb.log

# Proxy logs
tail -f logs/proxy_service.log
```

### Common Issues

1. **Port Already in Use**
   ```bash
   # Kill process on specific port
   lsof -ti:8000 | xargs kill -9
   ```

2. **MindsDB Not Starting**
   ```bash
   # Check MindsDB environment
   conda activate mindsdb-server
   mindsdb --version
   ```

3. **Backend Import Errors**
   ```bash
   # Check backend environment
   conda activate aishare-platform
   cd backend && python -c "from main import app; print('OK')"
   ```

## 📚 Key Features

- **Multi-Organization Support**: Secure data sharing across organizations
- **AI-Powered Analytics**: MindsDB integration for machine learning
- **Proxy Services**: Secure database connections with dedicated ports
- **Access Request System**: Professional workflow for data access
- **Real-time Notifications**: Track access requests and system events
- **Admin Management**: Comprehensive admin panel for system control

## 🛠️ Development

### Project Structure
```
simpleaisharing/
├── backend/           # FastAPI backend
├── frontend/          # Next.js frontend
├── logs/             # Service logs
├── docs/             # Documentation
└── *.sh              # Service management scripts
```

### Environment Requirements
- **Python**: 3.9+ (aishare-platform conda env)
- **MindsDB**: Latest (mindsdb-server conda env)
- **Node.js**: 18+ (for frontend)
- **Database**: SQLite (default) or PostgreSQL

For detailed documentation, see the individual markdown files in the project root.