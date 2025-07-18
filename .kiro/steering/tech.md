# Technology Stack

## Backend (Python/FastAPI)
- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM with SQLite database
- **Pydantic** - Data validation using Python type annotations
- **JWT Authentication** - Secure token-based authentication
- **MindsDB** - AI/ML engine for creating and managing models
- **Google Gemini** - AI chat and natural language processing
- **Uvicorn** - ASGI server implementation

## Frontend (Next.js/TypeScript)
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API calls
- **Lucide React** - Icon library

## Development Environment
- **Python 3.9+** with Conda environment management
- **Node.js 18+** for frontend development
- **SQLite** for development database

## ⚠️ IMPORTANT: Always Use Conda Environment

**ALWAYS activate the `aishare-platform` conda environment before any development work:**

```bash
conda activate aishare-platform
```

This environment contains all required Python dependencies and ensures consistent development setup.

## Common Commands

### Development Setup
```bash
# Create conda environment (one-time setup)
conda create -n aishare-platform python=3.9

# ALWAYS activate environment first
conda activate aishare-platform

# Backend setup
cd backend && pip install -r requirements.txt
python start.py

# Frontend setup (in separate terminal)
cd frontend && npm install
npm run dev

# Full development environment (recommended)
./start-dev.sh  # This script automatically activates conda env
```

### Testing
```bash
# ALWAYS activate conda environment first
conda activate aishare-platform

# All tests are located in the separate tests/ folder
cd tests

# Run all tests (recommended)
python run_all_tests.py

# Run specific test files
python test_backend.py
python test_frontend.py
python test_complete_system_fullflow_01_20250710_152829.py

# Run tests with shell script
./run_tests.sh

# Frontend tests (run from frontend directory)
cd ../frontend && npm test
```

### Database Operations
```bash
# ALWAYS activate conda environment first
conda activate aishare-platform

# Initialize database
cd backend && python -c "from app.core.init_db import init_db; init_db()"

# Run migrations
cd backend && python app/core/migration_*.py
```

## Key Dependencies
- **mindsdb** - Core AI/ML functionality
- **google-generativeai** - Gemini AI integration
- **python-jose** - JWT token handling
- **bcrypt** - Password hashing
- **pandas** - Data processing
- **sqlalchemy** - Database ORM

Always put test script into separate folder inside test and all md files into docs folder