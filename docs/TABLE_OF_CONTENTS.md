# Documentation Table of Contents

## 📚 Documentation Index

### Getting Started
- [README](./README.md) - Main documentation overview
- [Quick Start Guide](./QUICK_START.md) - Get up and running in 3 steps

### Configuration & Setup
- [Backend Startup Guide](./BACKEND_STARTUP_GUIDE.md) - Detailed backend service instructions
- [Storage Configuration](./STORAGE_CONFIGURATION.md) - Configure storage options
- [Simple Storage Guide](./SIMPLE_STORAGE_GUIDE.md) - Basic storage setup

### Features & Modes
- [Proxy Mode Guide](./PROXY_MODE_GUIDE.md) - Integrated proxy connector system

### Testing Guides
- [S3 Simple Testing](./S3_SIMPLE_TESTING.md) - Basic S3 testing procedures
- [S3 Testing Guide](./S3_TESTING_GUIDE.md) - Comprehensive S3 testing

## 🗂️ Documentation Organization

```
docs/
├── TABLE_OF_CONTENTS.md    # This file - Documentation index
├── README.md               # Main documentation hub
├── QUICK_START.md          # Quick start guide
├── BACKEND_STARTUP_GUIDE.md # Backend service guide
├── PROXY_MODE_GUIDE.md     # Proxy connector guide
├── STORAGE_CONFIGURATION.md # Storage setup guide
├── SIMPLE_STORAGE_GUIDE.md # Simple storage guide
├── S3_SIMPLE_TESTING.md    # S3 testing basics
└── S3_TESTING_GUIDE.md     # S3 testing advanced
```

## 📖 Reading Order for New Users

1. **Start Here**: [README](./README.md)
2. **Quick Setup**: [QUICK_START](./QUICK_START.md)
3. **Backend Details**: [BACKEND_STARTUP_GUIDE](./BACKEND_STARTUP_GUIDE.md)
4. **Storage Setup**: [STORAGE_CONFIGURATION](./STORAGE_CONFIGURATION.md)
5. **Advanced Features**: [PROXY_MODE_GUIDE](./PROXY_MODE_GUIDE.md)

## 🔍 Find Documentation by Topic

### Authentication & Security
- JWT Authentication - See [Backend Startup Guide](./BACKEND_STARTUP_GUIDE.md#authentication)
- API Security - See [Proxy Mode Guide](./PROXY_MODE_GUIDE.md#security)

### Database & Storage
- Local Storage - See [Simple Storage Guide](./SIMPLE_STORAGE_GUIDE.md)
- S3 Integration - See [S3 Testing Guide](./S3_TESTING_GUIDE.md)
- Database Connectors - See [Proxy Mode Guide](./PROXY_MODE_GUIDE.md#database-connectors)

### API & Endpoints
- REST API - See [Backend Startup Guide](./BACKEND_STARTUP_GUIDE.md#endpoints)
- Proxy Endpoints - See [Proxy Mode Guide](./PROXY_MODE_GUIDE.md#proxy-endpoints)
- API Documentation - Visit http://localhost:8000/docs

### Testing & Development
- S3 Testing - See [S3 Testing Guide](./S3_TESTING_GUIDE.md)
- Test Environment - See [Quick Start Guide](./QUICK_START.md#testing)

## 🚀 Quick Links

| Service | URL | Purpose |
|---------|-----|---------|
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| Backend | http://localhost:8000 | Main backend service |
| Frontend | http://localhost:3000 | React frontend (if running) |
| MindsDB | http://localhost:47334 | ML engine interface |

## 📝 Contributing to Documentation

When adding new documentation:
1. Create the markdown file in the `docs/` directory
2. Update this TABLE_OF_CONTENTS.md
3. Update the main README.md if needed
4. Follow the existing format and style
5. Include examples and code snippets where helpful

## 🔄 Version History

- **Current Version**: 2.0 (Integrated Proxy Mode)
- **Previous Version**: 1.0 (Upload Mode Only)

For version-specific documentation, check the git history or releases.