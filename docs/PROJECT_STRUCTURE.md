# AI Share Platform - Project Structure

## Overview
This document describes the clean, organized structure of the AI Share Platform after the fresh installation migration.

## Root Directory Structure
```
aishare-platform/
├── backend/                    # FastAPI backend application
├── frontend/                   # Next.js frontend application
├── storage/                    # Unified data storage
├── tests/                      # All test files and test data
├── docs/                       # Documentation files
├── migrations/                 # Database migration scripts
├── logs/                       # Application logs (runtime)
├── .env                        # Unified environment configuration
├── .env.example               # Environment template
├── setup_fresh_install.py     # Fresh installation script
├── start-dev.sh               # Development startup script
├── stop-dev.sh                # Development stop script
└── README.md                  # Main project documentation
```

## Backend Structure (`backend/`)
```
backend/
├── app/
│   ├── api/                   # API route handlers
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── datasets.py       # Dataset management
│   │   ├── organizations.py  # Organization management
│   │   ├── models.py         # ML model endpoints
│   │   ├── mindsdb.py        # MindsDB integration
│   │   ├── admin.py          # Admin panel endpoints
│   │   ├── analytics.py      # Analytics endpoints
│   │   ├── data_sharing.py   # Data sharing features
│   │   ├── data_connectors.py # Database connectors
│   │   └── file_handler.py   # File upload handling
│   ├── core/                 # Core functionality
│   │   ├── auth.py           # Authentication utilities
│   │   ├── config.py         # Application settings
│   │   ├── database.py       # Database connection
│   │   └── init_db.py        # Database initialization
│   ├── models/               # SQLAlchemy database models
│   │   ├── user.py           # User model
│   │   ├── dataset.py        # Dataset and related models
│   │   └── organization.py   # Organization models
│   ├── schemas/              # Pydantic request/response schemas
│   │   ├── user.py           # User schemas
│   │   ├── dataset.py        # Dataset schemas
│   │   └── organization.py   # Organization schemas
│   └── services/             # Business logic services
│       ├── mindsdb.py        # MindsDB service layer
│       ├── data_sharing.py   # Data sharing logic
│       ├── analytics.py      # Analytics service
│       ├── connector_service.py # Data connector service
│       ├── storage.py        # File storage service
│       ├── metadata.py       # Metadata extraction
│       ├── preview.py        # Data preview generation
│       └── download.py       # Download handling
├── migrations/               # Database migrations
├── .env                     # Backend-specific environment
├── main.py                  # FastAPI application entry point
├── start.py                 # Application startup script
└── requirements.txt         # Python dependencies
```

## Frontend Structure (`frontend/`)
```
frontend/
├── src/
│   ├── app/                  # Next.js App Router pages
│   │   ├── admin/           # Admin panel pages
│   │   ├── analytics/       # Analytics dashboard
│   │   ├── datasets/        # Dataset management pages
│   │   │   ├── upload-document/ # Document upload page
│   │   │   ├── connect/     # Data source connection
│   │   │   └── [id]/        # Dataset detail pages
│   │   ├── models/          # ML model pages
│   │   ├── organizations/   # Organization pages
│   │   ├── connections/     # Data connections page
│   │   ├── shared/          # Public sharing pages
│   │   ├── login/           # Authentication pages
│   │   └── layout.tsx       # Root layout component
│   ├── components/          # React components
│   │   ├── auth/            # Authentication components
│   │   ├── layout/          # Layout components
│   │   ├── datasets/        # Dataset-related components
│   │   │   ├── document-preview.tsx
│   │   │   └── dataset-list.tsx
│   │   ├── ui/              # Reusable UI components
│   │   │   └── DownloadComponent.tsx
│   │   └── DocumentUploader.tsx # Document upload component
│   └── lib/                 # Utilities and configurations
│       ├── api.ts           # API client configuration
│       ├── types.ts         # TypeScript type definitions
│       └── utils.ts         # Helper functions
├── public/                  # Static assets
├── .env.local              # Frontend environment variables
├── package.json            # Node.js dependencies
├── tailwind.config.js      # Tailwind CSS configuration
└── next.config.ts          # Next.js configuration
```

## Storage Structure (`storage/`)
```
storage/
├── aishare_platform.db     # Unified SQLite database
├── uploads/                # User uploaded files
├── documents/              # Processed document files
├── logs/                   # Application log files
└── backups/               # Database backups
```

## Tests Structure (`tests/`)
```
tests/
├── data/                   # Test data files
├── integration/            # Integration tests
├── csv_tests/             # CSV-specific tests
├── test_results/          # Test result outputs
├── test_backend.py        # Backend API tests
├── test_frontend.py       # Frontend tests
├── test_document_processing.py # Document processing tests
├── test_simple_document.py # Simple document tests
├── run_all_tests.py       # Test runner
└── README.md              # Testing documentation
```

## Documentation Structure (`docs/`)
```
docs/
├── PROJECT_STRUCTURE.md      # This file
├── ENHANCED_DATASET_MANAGEMENT.md # Feature documentation
├── IMPLEMENTATION_SUMMARY.md # Implementation details
├── DATASET_ML_MODELS_FEATURE.md # ML features
├── README.md                 # General documentation
├── Research.md               # Research notes
└── TODO.md                   # Future tasks
```

## Configuration Files

### Environment Configuration
- **`.env`** - Main unified environment configuration
- **`.env.example`** - Template for environment setup
- **`backend/.env`** - Backend-specific overrides
- **`frontend/.env.local`** - Frontend-specific variables

### Database Configuration
- **Unified Database**: `storage/aishare_platform.db`
- **Connection String**: `sqlite:///./storage/aishare_platform.db`
- **Migrations**: Located in `migrations/` directory

## Key Features by Directory

### Backend Features
- **Authentication & Authorization**: JWT-based auth with organization scoping
- **Dataset Management**: Upload, process, and manage various data formats
- **Document Processing**: PDF, DOCX, DOC, TXT, RTF, ODT support
- **Data Connectors**: MySQL, PostgreSQL, MongoDB, S3, and more
- **AI Integration**: MindsDB and Google Gemini integration
- **Data Sharing**: Secure sharing with expiration and passwords
- **Analytics**: Usage tracking and performance metrics

### Frontend Features
- **Modern UI**: Next.js 15 with Tailwind CSS
- **Document Upload**: Drag-and-drop with progress tracking
- **Data Visualization**: Charts and data previews
- **AI Chat Interface**: Chat with datasets and documents
- **Admin Dashboard**: User and organization management
- **Responsive Design**: Mobile-friendly interface

### Storage Features
- **Unified Database**: Single SQLite database for all data
- **File Management**: Organized file storage with metadata
- **Backup System**: Automated backup creation
- **Log Management**: Structured logging with rotation

## Development Workflow

### Setup Commands
```bash
# Fresh installation
python setup_fresh_install.py

# Start development environment
./start-dev.sh

# Stop development environment
./stop-dev.sh

# Run tests
cd tests && python run_all_tests.py
```

### Database Operations
```bash
# Run migrations
python migrations/fresh_install_migration.py

# Backup database
cp storage/aishare_platform.db storage/backups/backup_$(date +%Y%m%d_%H%M%S).db
```

## Security Considerations

### Data Isolation
- Organization-scoped data access
- Role-based permissions
- Secure file storage

### Authentication
- JWT token-based authentication
- Password hashing with bcrypt
- Session management

### File Security
- File type validation
- Size limit enforcement
- Secure upload handling

## Performance Optimizations

### Database
- Indexed columns for fast queries
- Connection pooling
- Query optimization

### File Handling
- Background processing for large files
- Streaming uploads
- Caching for frequently accessed data

### Frontend
- Code splitting and lazy loading
- Image optimization
- Client-side caching

## Monitoring and Logging

### Log Files
- **Application Logs**: `storage/logs/app.log`
- **Error Logs**: `storage/logs/error.log`
- **Access Logs**: `storage/logs/access.log`

### Metrics
- API response times
- File processing success rates
- User activity tracking
- System resource usage

## Deployment Structure

### Development
- Local SQLite database
- File-based storage
- Hot reloading enabled

### Production
- PostgreSQL database (recommended)
- Cloud storage integration
- Load balancing and caching

## Migration from Old Structure

The fresh installation migration handles:
- ✅ Database consolidation
- ✅ File organization
- ✅ Configuration unification
- ✅ Test file organization
- ✅ Documentation structure

## Maintenance Tasks

### Regular Tasks
- Database backups
- Log rotation
- Dependency updates
- Security patches

### Monitoring
- Disk space usage
- Database performance
- API response times
- Error rates

---

This structure provides a clean, maintainable, and scalable foundation for the AI Share Platform with clear separation of concerns and organized file management.

*Last updated: July 17, 2025*