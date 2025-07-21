# AI Share Platform

A powerful AI-driven data sharing platform built with **FastAPI** and **Next.js**, powered by **MindsDB** for machine learning capabilities.

## 🚀 Tech Stack

### Backend (FastAPI)
- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM
- **JWT Authentication** - Secure token-based authentication
- **MindsDB** - AI/ML engine for creating and managing models
- **Pydantic** - Data validation using Python type annotations
- **Uvicorn** - ASGI server implementation

### Frontend (Next.js)
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API calls
- **Lucide React** - Beautiful icons

## 📁 Project Structure

```
simpleaisharing/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes
│   │   │   ├── auth.py        # Authentication endpoints
│   │   │   ├── admin.py       # Admin panel endpoints
│   │   │   └── mindsdb.py     # MindsDB integration endpoints
│   │   ├── core/              # Core functionality
│   │   │   ├── auth.py        # Authentication utilities
│   │   │   ├── config.py      # Application settings
│   │   │   ├── database.py    # Database connection
│   │   │   └── init_db.py     # Database initialization
│   │   ├── models/            # SQLAlchemy models
│   │   │   ├── user.py        # User model
│   │   │   └── config.py      # Configuration model
│   │   ├── schemas/           # Pydantic schemas
│   │   │   ├── user.py        # User schemas
│   │   │   └── config.py      # Configuration schemas
│   │   └── services/          # Business logic
│   │       └── mindsdb.py     # MindsDB service
│   ├── main.py                # FastAPI application entry point
│   ├── start.py               # Startup script
│   ├── .env                   # Environment variables
│   └── requirements.txt       # Python dependencies
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/               # App Router pages
│   │   ├── components/        # React components
│   │   │   ├── ui/            # UI components
│   │   │   ├── auth/          # Authentication components
│   │   │   ├── admin/         # Admin panel components
│   │   │   └── mindsdb/       # MindsDB components
│   │   └── lib/               # Utilities
│   │       ├── api.ts         # API client
│   │       └── utils.ts       # Helper functions
│   ├── package.json           # Node.js dependencies
│   └── tailwind.config.js     # Tailwind configuration
└── TODO.md                    # Project roadmap
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.12+
- Node.js 18+
- Anaconda/Miniconda

### Backend Setup

1. **Create conda environment:**
   ```bash
   conda create -n aishare-platform python=3.9 -y
   conda activate aishare-platform
   ```

2. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   # Edit .env file with your settings
   cp .env.example .env
   ```

4. **Initialize database and start server:**
   ```bash
   python start.py
   ```

   The backend will be available at: `http://localhost:8000`
   API documentation: `http://localhost:8000/docs`

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at: `http://localhost:3000`

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./app.db
BACKEND_CORS_ORIGINS=http://localhost:3000
MINDSDB_URL=http://127.0.0.1:47334
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=admin123
```

#### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🎯 Features

### Authentication
- [x] User registration and login
- [x] JWT token-based authentication
- [x] Role-based access control (Admin/User)
- [x] Secure password hashing

### Admin Panel
- [x] Configuration management
- [x] Google API key management
- [x] User management
- [x] System settings

### MindsDB Integration
- [x] Model creation and management
- [x] Database connections
- [x] SQL query execution
- [x] Prediction endpoints
- [x] Model deployment

### UI/UX
- [x] Modern responsive design
- [x] Tailwind CSS styling
- [x] Component-based architecture
- [x] TypeScript for type safety

## 🚀 Deployment

### Backend Deployment Options
- **Railway** - Recommended for FastAPI
- **Render** - Easy deployment with database
- **DigitalOcean App Platform** - Scalable option

### Frontend Deployment Options
- **Vercel** - Recommended for Next.js (optimal)
- **Cloudflare Pages** - Works with all frameworks
- **Netlify** - Alternative option

### Database Options
- **SQLite** - Development/small scale
- **PostgreSQL** - Production (Railway/Render)
- **Supabase** - Managed PostgreSQL option

## 📝 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user

### Admin
- `GET /api/v1/admin/config` - Get configurations
- `POST /api/v1/admin/config` - Create configuration
- `PUT /api/v1/admin/config/{key}` - Update configuration
- `POST /api/v1/admin/google-api-key` - Set Google API key

### MindsDB
- `GET /api/v1/mindsdb/status` - Check MindsDB status
- `GET /api/v1/mindsdb/models` - List models
- `POST /api/v1/mindsdb/models` - Create model
- `POST /api/v1/mindsdb/models/{name}/predict` - Make prediction
- `GET /api/v1/mindsdb/databases` - List databases
- `POST /api/v1/mindsdb/sql` - Execute SQL

## 🔐 Default Credentials

**Admin User:**
- Email: `admin@example.com`
- Password: `admin123`

> ⚠️ **Important:** Change these credentials in production!

## 🧪 Development

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Formatting
```bash
# Backend
black . && isort .

# Frontend
npm run lint
```

## 📚 Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [MindsDB Documentation](https://docs.mindsdb.com/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the existing issues on GitHub
2. Create a new issue with detailed description
3. Join our community discussions

---

**Happy coding! 🎉**