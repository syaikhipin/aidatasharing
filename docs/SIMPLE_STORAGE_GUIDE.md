# Simple Storage Configuration Guide

Your program supports **two simple storage options**:

## 🎯 **Two Simple Choices**

### Option 1: Local Storage (Default)
Store all files on your server's local disk.

```env
STORAGE_TYPE=local
STORAGE_DIR=./storage
```

**✅ Best for:**
- Development
- Small deployments
- Single server setups
- When you want simple file access

### Option 2: S3 Storage
Store all files in S3-compatible storage (AWS S3, IDrive e2, MinIO, etc.).

```env
STORAGE_TYPE=s3
S3_BUCKET_NAME=your_bucket_name
S3_ACCESS_KEY_ID=your_access_key
S3_SECRET_ACCESS_KEY=your_secret_key
S3_ENDPOINT_URL=your_s3_endpoint
S3_REGION=your_region
```

**✅ Best for:**
- Production deployments
- Cloud-native setups
- Multi-server environments
- Scalable storage needs

## ⚙️ **How to Configure**

### For Local Storage (Default)
Just ensure these are in your `.env`:

```env
STORAGE_TYPE=local
STORAGE_DIR=../storage
STORAGE_BASE_PATH=../storage
```

### For S3 Storage
Set these in your `.env`:

```env
STORAGE_TYPE=s3
S3_BUCKET_NAME=my-app-storage
S3_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
S3_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
S3_ENDPOINT_URL=https://s3.amazonaws.com
S3_REGION=us-east-1
```

## 🔄 **Migration Between Storage Types**

You can easily switch and migrate your data:

```bash
# Check current storage status
GET /api/admin/storage/status

# Migrate from local to S3
POST /api/admin/storage/migrate
{
  "target_backend": "s3"
}

# Migrate from S3 to local
POST /api/admin/storage/migrate
{
  "target_backend": "local"
}
```

## 🌐 **MindsDB Integration**

Both storage types work perfectly with MindsDB:

### Local Storage + MindsDB
MindsDB can access files directly from local storage paths.

### S3 Storage + MindsDB
MindsDB gets secure presigned URLs for S3 file access.

## 🔐 **Shared Downloads**

Your existing shared dataset functionality works with both:

- **Local Storage**: Files streamed through the API
- **S3 Storage**: Direct secure download links
- **Password protection**: Works with both
- **Multi-file datasets**: Supported on both
- **AI chat**: Works regardless of storage type

## 🚀 **Quick Start**

### Want to use local storage? (Default)
No configuration needed! It just works.

### Want to use S3 storage?

1. **Set up your S3 bucket**
2. **Get your credentials** 
3. **Update your `.env`**:
   ```env
   STORAGE_TYPE=s3
   S3_BUCKET_NAME=your_bucket
   S3_ACCESS_KEY_ID=your_key
   S3_SECRET_ACCESS_KEY=your_secret
   S3_ENDPOINT_URL=your_endpoint
   ```
4. **Restart your application**
5. **Migrate existing files** (if needed):
   ```bash
   POST /api/admin/storage/migrate {"target_backend": "s3"}
   ```

That's it! Simple and clear. ✨

## ❓ **FAQ**

**Q: Can I use both local and S3 at the same time?**
A: No, choose one. This keeps it simple and avoids confusion.

**Q: How do I switch from local to S3?**
A: Change `STORAGE_TYPE=s3`, configure S3 settings, restart, then migrate files.

**Q: Will my shared links still work after switching storage?**
A: Yes! The shared download functionality adapts automatically.

**Q: Does this work with MindsDB?**
A: Yes! MindsDB can access files from either storage type.

**Q: Is S3 compatible with other providers?**
A: Yes! Works with AWS S3, IDrive e2, MinIO, DigitalOcean Spaces, etc.