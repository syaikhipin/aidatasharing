# Project Structure

## Root Directory Organization
```
simpleaisharing/
├── backend/           # FastAPI backend application
├── frontend/          # Next.js frontend application  
├── tests/             # Comprehensive test suite
├── logs/              # Application logs and archives
├── .kiro/             # Kiro AI assistant configuration
├── start-dev.sh       # Development environment startup script
└── stop_dev.sh        # Development environment shutdown script
```

## Backend Structure (`backend/`)
```
backend/
├── app/
│   ├── api/           # API route handlers
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── datasets.py       # Dataset management
│   │   ├── organizations.py  # Organization management
│   │   ├── models.py         # ML model endpoints
│   │   ├── mindsdb.py        # MindsDB integration
│   │   ├── admin.py          # Admin panel endpoints
│   │   ├── analytics.py      # Analytics endpoints
│   │   ├── data_sharing.py   # Data sharing features
│   │   └── data_connectors.py # Database connectors
│   ├── core/          # Core functionality
│   │   ├── auth.py           # Authentication utilities
│   │   ├── config.py         # Application settings
│   │   ├── database.py       # Database connection
│   │   └── init_db.py        # Database initialization
│   ├── models/        # SQLAlchemy database models
│   │   ├── user.py           # User model
│   │   ├── dataset.py        # Dataset and related models
│   │   └── organization.py   # Organization models
│   ├── schemas/       # Pydantic request/response schemas
│   │   ├── user.py           # User schemas
│   │   ├── dataset.py        # Dataset schemas
│   │   └── organization.py   # Organization schemas
│   └── services/      # Business logic services
│       ├── mindsdb.py        # MindsDB service layer
│       ├── data_sharing.py   # Data sharing logic
│       └── analytics.py      # Analytics service
├── main.py            # FastAPI application entry point
├── start.py           # Application startup script
└── requirements.txt   # Python dependencies
```

## Frontend Structure (`frontend/`)
```
frontend/
├── src/
│   ├── app/           # Next.js App Router pages
│   │   ├── admin/            # Admin panel pages
│   │   ├── analytics/        # Analytics dashboard
│   │   ├── datasets/         # Dataset management pages
│   │   ├── models/           # ML model pages
│   │   ├── organizations/    # Organization pages
│   │   ├── login/            # Authentication pages
│   │   └── layout.tsx        # Root layout component
│   ├── components/    # React components
│   │   ├── auth/             # Authentication components
│   │   ├── layout/           # Layout components
│   │   └── ui/               # Reusable UI components
│   └── lib/           # Utilities and configurations
│       ├── api.ts            # API client configuration
│       └── utils.ts          # Helper functions
├── package.json       # Node.js dependencies
└── tailwind.config.js # Tailwind CSS configuration
```

## Key Architectural Patterns

### Backend Patterns
- **Layered Architecture**: API → Services → Models → Database
- **Dependency Injection**: FastAPI's dependency system for database sessions and auth
- **Organization-Scoped Data**: All data operations filtered by organization context
- **Soft Delete Pattern**: Models support soft deletion with `is_deleted` flags
- **Service Layer**: Business logic separated from API handlers

### Frontend Patterns
- **App Router**: Next.js 13+ file-based routing
- **Component Composition**: Reusable UI components with Tailwind CSS
- **Context Providers**: Authentication state management
- **Protected Routes**: Route-level authentication guards

### Database Patterns
- **Foreign Key Relationships**: Proper relational data modeling
- **Enum Types**: Consistent status and type definitions
- **Audit Fields**: Created/updated timestamps on all models
- **JSON Columns**: Flexible metadata storage

### API Patterns
- **RESTful Design**: Standard HTTP methods and status codes
- **Pydantic Validation**: Request/response schema validation
- **JWT Authentication**: Stateless token-based auth
- **CORS Configuration**: Proper cross-origin setup for frontend