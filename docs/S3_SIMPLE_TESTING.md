# S3 Storage Testing Guide

Quick guide to test your simplified S3 storage configuration.

## ✅ **Test Local Storage (Default)**

1. **Check your `.env`:**
   ```env
   STORAGE_TYPE=local
   STORAGE_DIR=../storage
   ```

2. **Start the application**

3. **Upload a file** via the web interface

4. **Verify**: File should be in your `storage` directory

## ✅ **Test S3 Storage**

1. **Configure `.env`:**
   ```env
   STORAGE_TYPE=s3
   S3_BUCKET_NAME=test-bucket
   S3_ACCESS_KEY_ID=your_key_id
   S3_SECRET_ACCESS_KEY=your_secret
   S3_ENDPOINT_URL=https://s3.amazonaws.com
   S3_REGION=us-east-1
   ```

2. **Start the application**

3. **Check the logs** - should see:
   ```
   ✅ Initialized S3 storage backend (bucket: test-bucket)
   ```

4. **Upload a file** via the web interface

5. **Verify**: File should be in your S3 bucket

## 🔧 **Test Migration**

1. **Start with local storage**
2. **Upload some test files**
3. **Switch to S3** (update `.env` and restart)
4. **Migrate files**:
   ```bash
   curl -X POST http://localhost:8000/api/admin/storage/migrate \
   -H "Content-Type: application/json" \
   -H "Authorization: Bearer your_admin_token" \
   -d '{"target_backend": "s3"}'
   ```

## 🌐 **Test Shared Downloads**

1. **Create a shared dataset**
2. **Share the link**
3. **Download from shared page**
4. **Should work with both local and S3!**

## ❌ **Troubleshooting**

### S3 Connection Issues
```
Error: S3 initialization failed, falling back to local storage
```
**Fix**: Check your S3 credentials and bucket name

### File Not Found
```
Error: File not found in S3: org_1/dataset_1.csv
```
**Fix**: Run migration to move files to S3

### Permission Denied
```
Error: Access denied to bucket
```
**Fix**: Check your S3 access key permissions

That's it! Simple testing for simple storage. 🎯