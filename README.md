# AI Share Platform

A comprehensive AI-powered data sharing platform that enables organizations to securely share, analyze, and build machine learning models on their data.

## 🚀 Quick Start

### Fresh Installation
```bash
# Clone the repository
git clone <repository-url>
cd simpleaisharing

# Run fresh installation setup
python setup_fresh_install.py

# Start development environment
./start-dev.sh
```

### Access the Platform
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Default Admin Credentials
- **Email**: admin@example.com
- **Password**: admin123

## ✨ Key Features

### 📊 Dataset Management
- **Multiple Formats**: CSV, JSON, Excel, PDF, DOCX, DOC, TXT, RTF, ODT
- **Document Processing**: Automatic text extraction and analysis
- **Schema Detection**: Automatic data structure analysis
- **Preview Generation**: Smart data previews and summaries

### 🔗 Data Connectors
- **Databases**: MySQL, PostgreSQL, MongoDB, Snowflake, BigQuery, Redshift, ClickHouse
- **Cloud Storage**: AWS S3 integration
- **API Sources**: REST API data connectors
- **File Systems**: Local and network file system access

### 🤖 AI Integration
- **MindsDB**: Advanced ML model creation and management
- **Google Gemini**: Natural language processing and chat
- **Document Chat**: AI-powered document Q&A
- **Data Insights**: Automated analysis and recommendations

### 🔐 Security & Sharing
- **Organization Scoping**: Multi-tenant data isolation
- **Secure Sharing**: Password-protected, expiring share links
- **Role-Based Access**: Granular permission management
- **Audit Logging**: Comprehensive activity tracking

### 📈 Analytics & Monitoring
- **Usage Analytics**: Real-time usage monitoring
- **Performance Metrics**: System performance tracking
- **Data Quality**: Automated data quality assessment
- **User Activity**: Detailed user activity logs

### ⚙️ Environment Management
- **Unified Configuration**: Single .env file managed from admin panel
- **Category-based Settings**: Organized environment variables
- **Real-time Updates**: Update configuration without restart
- **Security**: Masked sensitive values

## 🏗️ Architecture

### Backend (FastAPI)
- **FastAPI**: Modern, fast web framework
- **SQLAlchemy**: Advanced ORM with SQLite support
- **Pydantic**: Data validation and serialization
- **JWT Authentication**: Secure token-based authentication
- **Background Tasks**: Async processing for large operations

### Frontend (Next.js)
- **Next.js 15**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Responsive Design**: Mobile-friendly interface
- **Real-time Updates**: Live data synchronization

### Database
- **Unified Database**: Single SQLite database for all data
- **Future Flexibility**: Easily switchable to PostgreSQL or other databases
- **Migration System**: Automated schema updates
- **Data Isolation**: Organization-scoped data security

## 📁 Project Structure

```
simpleaisharing/
├── backend/                 # FastAPI backend application
│   ├── app/                # Application code
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Core functionality
│   │   ├── models/        # Database models
│   │   ├── schemas/       # Pydantic schemas
│   │   └── services/      # Business logic
│   └── requirements.txt   # Python dependencies
├── frontend/               # Next.js frontend application
│   ├── src/               # Source code
│   │   ├── app/          # Next.js pages
│   │   ├── components/   # React components
│   │   └── lib/          # Utilities
│   └── package.json      # Node.js dependencies
├── storage/               # Data storage
│   ├── aishare_platform.db # Unified SQLite database
│   ├── uploads/          # File uploads
│   └── documents/        # Document processing
├── migrations/           # Database migrations
├── .env                 # Unified environment configuration
└── README.md           # This file
```

## 🛠️ Development

### Prerequisites
- **Python 3.12+** (recommended: conda environment)
- **Node.js 18+**
- **Git**

### Setup Development Environment
```bash
# Create conda environment (recommended)
conda create -n aishare-platform python=3.9
conda activate aishare-platform

# Run fresh installation
python setup_fresh_install.py

# Start development servers
./start-dev.sh
```

### Development Commands
```bash
# Start development environment
./start-dev.sh

# Stop development environment
./stop-dev.sh

# Backend only
cd backend && python start.py

# Frontend only
cd frontend && npm run dev
```

### Environment Configuration

The platform uses a unified `.env` file for all configuration. You can manage environment variables through:

1. **Admin Panel**: Use the Environment Settings in the admin panel (recommended)
2. **Direct Edit**: Edit the `.env` file directly

Key configuration categories:
- **Database**: SQLite database configuration
- **Security**: JWT and authentication settings
- **API**: Google AI and external API keys
- **AI Models**: Gemini and MindsDB configuration
- **Data Sharing**: Sharing and collaboration settings
- **File Upload**: Upload limits and file types
- **Connectors**: Data connector settings
- **AWS**: S3 and cloud service configuration

## 🔧 Configuration

### Environment Variables
All environment variables are managed through the unified `.env` file and can be configured via the admin panel:

- **DATABASE_URL**: SQLite database path (unified storage)
- **GOOGLE_API_KEY**: Google AI API key for Gemini integration
- **MINDSDB_URL**: MindsDB server URL
- **SECRET_KEY**: JWT signing secret
- **MAX_FILE_SIZE_MB**: Maximum file upload size
- **ALLOWED_FILE_TYPES**: Supported file formats

### Admin Panel Management
Access environment settings through:
1. Login as admin (admin@aishare.com / admin123)
2. Go to Admin Panel
3. Click "Environment Settings"
4. Edit variables by category
5. Changes take effect immediately

## 🚀 Deployment

### Development Deployment
```bash
# Start with development configuration
./start-dev.sh
```

### Production Deployment
1. Update `.env` with production configuration via admin panel
2. Set `NODE_ENV=production`
3. Configure external database if needed (PostgreSQL)
4. Set up cloud storage (S3) if required
5. Configure reverse proxy (nginx)
6. Set up SSL certificates

### Docker Deployment (Coming Soon)
```bash
# Build and run with Docker
docker-compose up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for frontend development
- Write tests for new features
- Update documentation for changes
- Follow conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Issues**: Create an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions

### Common Issues
- **Database Connection**: Ensure SQLite file permissions are correct
- **Port Conflicts**: Check if ports 3000/8000 are available
- **Dependencies**: Run `pip install -r backend/requirements.txt`
- **Environment**: Use admin panel to configure environment variables

## 🎯 Roadmap

### Current Version (v1.0)
- ✅ Core dataset management
- ✅ Document processing
- ✅ Data connectors
- ✅ AI chat integration
- ✅ Secure sharing
- ✅ Unified environment management

### Upcoming Features (v1.1)
- 🔄 Advanced document analysis (OCR, table extraction)
- 🔄 More database connectors (Oracle, SQL Server)
- 🔄 Enhanced AI models and analysis
- 🔄 Real-time collaboration features
- 🔄 Advanced analytics dashboard

### Future Plans (v2.0)
- 🔮 Machine learning pipeline automation
- 🔮 Advanced data visualization
- 🔮 API marketplace
- 🔮 Enterprise SSO integration
- 🔮 Multi-cloud deployment

---

**AI Share Platform** - Empowering organizations with intelligent data sharing and AI-driven insights.

*Built with ❤️ using FastAPI, Next.js, SQLite, and modern AI technologies.*