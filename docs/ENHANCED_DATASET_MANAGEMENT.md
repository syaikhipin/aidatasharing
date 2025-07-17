# Enhanced Dataset Management System

## Overview

The AI Share Platform now includes comprehensive dataset management capabilities with support for multiple data sources, document processing, and advanced data connectors.

## New Features

### 1. Document Processing
- **Supported Formats**: PDF, DOCX, DOC, TXT, RTF, ODT
- **Text Extraction**: Automatic text extraction with metadata
- **AI Chat**: Create AI models for document Q&A
- **Preview**: Generate text previews for quick review

### 2. Data Connectors
- **Database Support**: MySQL, PostgreSQL, MongoDB, Snowflake, BigQuery, Redshift, ClickHouse
- **Cloud Storage**: AWS S3 integration
- **API Connectors**: REST API data sources
- **File System**: Local file system connectors

### 3. Enhanced Dataset Features
- **Schema Detection**: Automatic schema analysis
- **Quality Metrics**: Data quality scoring and analysis
- **Preview Generation**: Smart data previews
- **Metadata Management**: Comprehensive metadata storage

## API Endpoints

### Document Processing
```
POST /api/data-connectors/document
- Upload and process document files
- Supports multipart/form-data
- Creates dataset with extracted text and metadata
```

### Data Connectors
```
POST /api/data-connectors
- Create new database/cloud connectors
- Validate connection parameters
- Test connectivity

GET /api/data-connectors/supported-types
- List supported connector types
- Get configuration requirements

POST /api/data-connectors/{id}/create-dataset
- Create dataset from connector source
- Specify table/query for data extraction
```

## Frontend Components

### 1. DocumentUploader Component
- Drag-and-drop file upload
- Progress tracking
- Format validation
- Real-time feedback

### 2. Data Source Connection
- Multi-tab interface for different connectors
- Form validation
- Connection testing
- Configuration management

### 3. Enhanced Dataset Views
- Document preview for text files
- Metadata display
- Quality metrics visualization
- Schema information

## Database Schema Updates

### New Dataset Fields
```sql
-- Document-specific fields
document_type VARCHAR          -- pdf, docx, doc, etc.
page_count INTEGER            -- Number of pages
word_count INTEGER            -- Word count
extracted_text TEXT           -- Extracted text content
text_extraction_method VARCHAR -- Extraction method used

-- Enhanced metadata
schema_metadata JSON          -- Schema information
quality_metrics JSON          -- Data quality scores
column_statistics JSON        -- Column-level statistics
```

### New DatasetType Enums
- `PDF` - PDF documents
- `DOCX` - Word documents  
- `S3_BUCKET` - S3 bucket data

## Usage Examples

### 1. Upload Document
```typescript
const formData = new FormData();
formData.append('file', file);
formData.append('dataset_name', 'My Document');
formData.append('description', 'Document description');
formData.append('sharing_level', 'PRIVATE');

const response = await api.post('/data-connectors/document', formData);
```

### 2. Connect to MySQL Database
```typescript
const connector = {
  name: 'Production DB',
  description: 'Main production database',
  connector_type: 'mysql',
  connection_config: {
    host: 'localhost',
    port: 3306,
    database: 'myapp'
  },
  credentials: {
    user: 'username',
    password: 'password'
  }
};

const response = await api.post('/data-connectors', connector);
```

### 3. Create Dataset from Connector
```typescript
const dataset = await api.post(`/data-connectors/${connectorId}/create-dataset`, {
  table_or_query: 'users',
  dataset_name: 'User Data',
  description: 'User information dataset',
  sharing_level: 'ORGANIZATION'
});
```

## Document Processing Libraries

### Required Dependencies
```bash
# PDF processing
pip install PyMuPDF==1.23.7

# DOCX processing  
pip install python-docx==1.0.1

# DOC processing
pip install docx2txt==0.8

# RTF processing
pip install striprtf==0.0.26

# ODT processing
pip install odfpy==1.4.1
```

### Database Connectors
```bash
# MySQL
pip install pymysql==1.1.0

# PostgreSQL
pip install psycopg2-binary==2.9.9

# MongoDB
pip install pymongo==4.6.1

# AWS S3
pip install boto3==1.34.29

# Snowflake
pip install snowflake-connector-python==3.5.0

# BigQuery
pip install google-cloud-bigquery==3.17.2

# Redshift
pip install redshift-connector==2.0.918

# ClickHouse
pip install clickhouse-driver==0.2.6
```

## Configuration

### Environment Variables
```bash
# MindsDB Configuration
MINDSDB_URL=http://localhost:47334
MINDSDB_USERNAME=mindsdb
MINDSDB_PASSWORD=

# Document Storage
DOCUMENT_STORAGE_PATH=/app/storage/documents
MAX_DOCUMENT_SIZE=50MB

# Connector Settings
CONNECTOR_TIMEOUT=30
MAX_CONNECTORS_PER_ORG=10
```

### Frontend Configuration
```typescript
// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Upload Limits
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const SUPPORTED_DOCUMENT_TYPES = ['pdf', 'docx', 'doc', 'txt', 'rtf', 'odt'];
```

## Security Considerations

### 1. File Upload Security
- File type validation
- Size limits enforcement
- Virus scanning (recommended)
- Secure file storage

### 2. Database Connections
- Encrypted credential storage
- Connection timeout limits
- IP whitelisting support
- SSL/TLS enforcement

### 3. Data Access Control
- Organization-level isolation
- Role-based permissions
- Audit logging
- Share link expiration

## Performance Optimization

### 1. Document Processing
- Background processing for large files
- Text extraction caching
- Preview generation optimization
- Memory usage monitoring

### 2. Database Connectors
- Connection pooling
- Query optimization
- Result caching
- Timeout management

### 3. Frontend Performance
- Lazy loading for large datasets
- Progressive file uploads
- Client-side caching
- Optimistic UI updates

## Monitoring and Logging

### Key Metrics
- Document processing success rate
- Connector connection health
- Dataset creation frequency
- Error rates by connector type

### Log Categories
- Document processing logs
- Connector operation logs
- Database migration logs
- API request/response logs

## Troubleshooting

### Common Issues

1. **Document Processing Fails**
   - Check file format support
   - Verify file size limits
   - Review extraction library installation

2. **Connector Connection Fails**
   - Validate connection parameters
   - Check network connectivity
   - Verify credentials

3. **Dataset Creation Errors**
   - Review MindsDB connectivity
   - Check database permissions
   - Validate schema information

### Debug Commands
```bash
# Test document processing
python test_document_processing.py

# Check connector health
python -c "from backend.app.services.connector_service import ConnectorService; print('Connectors available')"

# Verify database migration
python backend/migrations/versions/migration_20250717_160000_add_document_support.py
```

## Future Enhancements

### Planned Features
1. **Advanced Document Analysis**
   - OCR for scanned documents
   - Table extraction from PDFs
   - Image analysis and description

2. **Enhanced Connectors**
   - Elasticsearch integration
   - Apache Kafka streams
   - GraphQL API connectors

3. **AI-Powered Features**
   - Automatic data categorization
   - Smart schema suggestions
   - Anomaly detection

4. **Collaboration Tools**
   - Dataset annotations
   - Collaborative filtering
   - Version control for datasets

## Support

For issues or questions regarding the enhanced dataset management system:

1. Check the troubleshooting section above
2. Review the API documentation
3. Check system logs for error details
4. Contact the development team with specific error messages

---

*Last updated: July 17, 2025*