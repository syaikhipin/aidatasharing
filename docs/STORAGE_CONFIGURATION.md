# Storage Configuration Guide

This document explains how to configure and use the enhanced dual storage system in the AI Share Platform.

## Overview

The platform now supports **multiple storage strategies** that allow you to use both local and S3 storage simultaneously, providing maximum flexibility and compatibility with MindsDB.

## 🚀 Storage Strategies

### Available Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `local_primary` | Store all files locally (default) | Small datasets, development |
| `s3_primary` | Store files in S3 with local fallback | Cloud-first, scalable storage |
| `hybrid` | Large files (>10MB) in S3, small files locally | Mixed workloads, cost optimization |
| `redundant` | Store files in both local and S3 | Maximum data protection |

## ⚙️ Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Storage Strategy (New Feature!)
STORAGE_STRATEGY=local_primary

# Options:
# - local_primary: Store files locally (default)
# - s3_primary: Store files in S3 with local fallback
# - hybrid: Large files (>10MB) in S3, small files locally
# - redundant: Store files in both local and S3 for backup

# Hybrid Storage Configuration
HYBRID_SIZE_THRESHOLD_MB=10

# S3 Configuration (works with AWS S3, IDrive e2, MinIO, etc.)
S3_ENDPOINT_URL=your_s3_endpoint
S3_BUCKET_NAME=your_bucket_name
S3_ACCESS_KEY_ID=your_access_key
S3_SECRET_ACCESS_KEY=your_secret_key
S3_REGION=your_region
S3_USE_SSL=true
S3_ADDRESSING_STYLE=path
```

### MindsDB Integration

The system automatically integrates with MindsDB's `permanent_storage` configuration:

```json
{
  "permanent_storage": {
    "location": "s3",
    "bucket": "your-mindsdb-bucket"
  },
  "paths": {
    "root": "/path/to/storage",
    "content": "/path/to/content",
    "storage": "/path/to/storage"
  }
}
```

## 🔧 Usage Examples

### 1. Local-Only Storage (Default)

```env
STORAGE_STRATEGY=local_primary
STORAGE_DIR=./storage
```

**Best for**: Development, small datasets, single-server deployments

### 2. S3-Primary with Local Fallback

```env
STORAGE_STRATEGY=s3_primary
S3_BUCKET_NAME=my-app-bucket
S3_ACCESS_KEY_ID=your_access_key
S3_SECRET_ACCESS_KEY=your_secret_key
S3_ENDPOINT_URL=https://s3.amazonaws.com
```

**Best for**: Cloud deployments, scalable storage, multi-server setups

### 3. Smart Hybrid Storage

```env
STORAGE_STRATEGY=hybrid
HYBRID_SIZE_THRESHOLD_MB=10
# Configure both local and S3 settings
```

**Best for**: Mixed workloads, cost optimization, performance tuning

### 4. Redundant Storage (Maximum Protection)

```env
STORAGE_STRATEGY=redundant
# Configure both local and S3 settings
```

**Best for**: Critical data, backup requirements, high availability

## 🔄 Storage Migration

The platform includes built-in migration tools to move data between storage backends.

### API Endpoints

```bash
# Check storage status
GET /api/admin/storage/status

# Migrate all datasets to S3
POST /api/admin/storage/migrate
{
  "target_backend": "s3"
}

# Migrate specific datasets
POST /api/admin/storage/migrate
{
  "target_backend": "local",
  "dataset_ids": [1, 2, 3]
}

# Verify storage integrity
POST /api/admin/storage/verify

# Get storage recommendations
GET /api/admin/storage/recommendations
```

### Programmatic Migration

```python
from app.utils.storage_migration import migration_service

# Migrate a specific dataset
result = await migration_service.migrate_dataset_files(
    dataset_id=123, 
    target_backend="s3", 
    db=db_session
)

# Migrate all datasets
result = await migration_service.migrate_all_datasets("s3", db_session)
```

## 🔍 Monitoring & Management

### Storage Status Check

```python
from app.services.storage import storage_service

# Get current backend information
backend_info = storage_service.get_backend_info()
print(f"Current backend: {backend_info['backend_type']}")
print(f"Storage type: {backend_info['storage_type']}")
```

### Storage Verification

The system can automatically verify that all database file references have corresponding physical files:

```bash
POST /api/admin/storage/verify
```

This will:
- Check all dataset file references
- Identify missing files
- Clean up orphaned files
- Report integrity issues

## 🚨 Troubleshooting

### Common Issues

#### 1. S3 Connection Failed
```
Error: S3 initialization failed, falling back to local storage
```

**Solution**: Check your S3 credentials and endpoint URL:
```env
S3_ENDPOINT_URL=https://your-s3-endpoint.com
S3_ACCESS_KEY_ID=your_access_key
S3_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=your_bucket
```

#### 2. File Not Found During Migration
```
Error: File not found in local storage: org_1/dataset_1.csv
```

**Solution**: Run storage verification first:
```bash
POST /api/admin/storage/verify
```

#### 3. Hybrid Strategy Not Working
```
Error: Large files still being stored locally
```

**Solution**: Check your threshold setting:
```env
HYBRID_SIZE_THRESHOLD_MB=10  # Files > 10MB will go to S3
```

## 📊 Shared Downloads Compatibility

All storage strategies work seamlessly with the shared download functionality:

- **Local Storage**: Files served via FastAPI streaming
- **S3 Storage**: Direct presigned URLs for faster downloads
- **Hybrid/Redundant**: Automatic fallback between backends

### Shared Page Features

The shared dataset pages (`/shared/[token]`) automatically:
- Detect storage backend
- Generate appropriate download URLs
- Handle password-protected access
- Support multi-file dataset downloads
- Provide AI chat integration

## 🏗️ Architecture

### Storage Service Hierarchy

```
StorageService
├── LocalStorageBackend
├── S3StorageBackend
└── HybridStorageBackend
    ├── LocalStorageBackend (always available)
    └── S3StorageBackend (when configured)
```

### File Flow

1. **Upload**: Files are stored according to the configured strategy
2. **Access**: Files are retrieved with automatic fallback
3. **Sharing**: Shared links work regardless of storage backend
4. **Migration**: Files can be moved between backends

## 🔐 Security Considerations

### Local Storage
- Files stored in configured directory
- Access controlled by filesystem permissions
- Served through authenticated API endpoints

### S3 Storage
- Files stored with encryption in transit
- Access via presigned URLs (secure, time-limited)
- IAM policies control bucket access
- SSL/TLS encryption supported

### Hybrid/Redundant
- Combines security features of both backends
- Redundant storage provides additional data protection
- Automatic failover ensures availability

## 🚀 Performance Optimization

### Recommendations by Use Case

| Use Case | Recommended Strategy | Reasoning |
|----------|---------------------|-----------|
| Development | `local_primary` | Fastest access, simple setup |
| Small Production (<1GB) | `local_primary` | Cost-effective, good performance |
| Large Production (>1GB) | `s3_primary` or `hybrid` | Scalable, cost-effective |
| Critical Systems | `redundant` | Maximum data protection |
| Multi-region | `s3_primary` | Better global access |
| Cost-sensitive | `hybrid` | Optimize costs by file size |

## 🔄 MindsDB Compatibility

The enhanced storage system maintains full compatibility with MindsDB:

1. **File URLs**: Automatically generates MindsDB-compatible URLs
2. **Path Resolution**: Works with MindsDB's path configuration
3. **Access Control**: Respects MindsDB's security model
4. **Performance**: Optimized for MindsDB's access patterns

### MindsDB Configuration Example

```json
{
  "permanent_storage": {
    "location": "s3",
    "bucket": "mindsdb-storage"
  },
  "paths": {
    "root": "/opt/mindsdb",
    "content": "/opt/mindsdb/content",
    "storage": "/opt/mindsdb/storage"
  }
}
```

The platform will automatically:
- Read this configuration
- Set up appropriate storage backends  
- Ensure file accessibility for MindsDB
- Handle authentication and permissions

## 📞 Support

For additional help with storage configuration:

1. Check the application logs for detailed error messages
2. Use the storage verification endpoint to diagnose issues
3. Review the storage recommendations for optimization tips
4. Consult the troubleshooting section for common problems

## 🔄 Migration Guide

### From Single Storage to Hybrid

1. **Current Setup**: `STORAGE_TYPE=local`
2. **Add S3 Configuration**:
   ```env
   S3_BUCKET_NAME=your_bucket
   S3_ACCESS_KEY_ID=your_key
   S3_SECRET_ACCESS_KEY=your_secret
   ```
3. **Switch Strategy**: `STORAGE_STRATEGY=hybrid`
4. **Restart Application**
5. **Verify**: Use `/api/admin/storage/status` to confirm

### From Local to S3

1. **Configure S3** (as above)
2. **Set Strategy**: `STORAGE_STRATEGY=s3_primary`
3. **Restart Application**
4. **Migrate Data**: `POST /api/admin/storage/migrate {"target_backend": "s3"}`
5. **Verify**: Check that files are accessible

This enhanced storage system provides the flexibility you need while maintaining full compatibility with MindsDB and ensuring your shared downloads work seamlessly regardless of storage backend!