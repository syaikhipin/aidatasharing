# 🚀 S3 Storage Testing Guide

This guide will help you test the new dual storage system (Local + S3) with your existing IDrive e2 configuration.

## 📋 Prerequisites

Your `.env` file is already configured with:
- ✅ IDrive e2 credentials (entrust bucket)
- ✅ New storage strategy options
- ✅ Hybrid storage threshold set to 5MB

## 🎯 Testing Steps

### 1. **Access the Storage Management Interface**

1. Start your backend server: `cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`
2. Start your frontend: `cd frontend && npm run dev`
3. Navigate to: **http://localhost:3000/admin/storage**
4. Login as admin if needed

### 2. **Check Current Storage Status**

The storage management page will show:
- Current strategy: `hybrid` (files >5MB go to S3)
- Local backend: ✅ Available  
- S3 backend: ✅ Available (if IDrive e2 credentials work)
- Storage recommendations based on your data

### 3. **Test Different Storage Strategies**

Edit your `.env` file and restart the backend to test:

#### **Test 1: Local-Only Storage**
```env
STORAGE_STRATEGY=local_primary
```
- All files stored locally
- Good for testing baseline functionality

#### **Test 2: S3-Primary Storage** 
```env
STORAGE_STRATEGY=s3_primary  
```
- All files go to IDrive e2 S3
- Falls back to local if S3 fails

#### **Test 3: Hybrid Storage**
```env
STORAGE_STRATEGY=hybrid
HYBRID_SIZE_THRESHOLD_MB=5
```
- Files <5MB: stored locally
- Files >5MB: stored in S3

#### **Test 4: Redundant Storage**
```env
STORAGE_STRATEGY=redundant
```
- Files stored in BOTH local AND S3
- Maximum data protection

### 4. **Upload Test Files**

On the storage management page, use the **Storage Test Uploader**:

1. **Small files** (<5MB): Try CSV, JSON, small images
2. **Large files** (>5MB): Try large Excel files, PDFs, high-res images
3. Watch the results show where each file was stored

### 5. **Test Shared Downloads**

1. Upload some test files with different strategies
2. Enable sharing on a dataset
3. Visit the shared link
4. Test download functionality - should work regardless of storage backend

### 6. **Migration Testing**

1. Upload files with one strategy (e.g., `local_primary`)
2. Switch to another strategy (e.g., `s3_primary`)
3. Use the **Migration** section to move existing files
4. Verify files are accessible after migration

### 7. **Storage Verification**

Use the **Storage Verification** tool to:
- Check file integrity
- Find missing files
- Clean up orphaned files

## 🔍 What to Look For

### ✅ Success Indicators:
- Storage status shows both backends available
- Files upload successfully with correct strategy
- Download links work from shared pages
- Migration completes without errors
- AI chat works with shared datasets

### ⚠️ Common Issues:
- **S3 backend unavailable**: Check IDrive e2 credentials
- **Files not found**: Run storage verification
- **Upload failures**: Check file size limits and permissions
- **Shared downloads broken**: Verify file paths in database

## 🎛️ Admin Dashboard Features

### Storage Status Widget
- Shows current strategy and backend availability
- Quick access to storage management
- Real-time status updates

### Storage Management Page
- Live storage analytics
- Migration tools
- Verification utilities
- Testing components

## 📊 Testing Scenarios

### Scenario 1: Development to Production
1. Start with `local_primary` for development
2. Upload test datasets
3. Switch to `s3_primary` for production
4. Migrate existing files to S3
5. Verify everything works

### Scenario 2: Cost Optimization
1. Use `hybrid` strategy
2. Set threshold to 10MB: `HYBRID_SIZE_THRESHOLD_MB=10`
3. Upload mix of small and large files
4. Verify small files stay local, large go to S3

### Scenario 3: High Availability
1. Use `redundant` strategy
2. Upload critical datasets
3. Verify files exist in both locations
4. Test failover (temporarily disable S3)

## 🚨 Troubleshooting

### IDrive e2 Connection Issues
```bash
# Test S3 connection manually
curl -X GET "https://g7h4.fra3.idrivee2-51.com"
```

### Backend Logs
```bash
# Check backend logs for storage errors
tail -f backend/logs/app.log
```

### Database Issues
```bash
# Check database for file references
# Use the admin interface or connect to your PostgreSQL
```

## 🎉 Success Checklist

- [ ] Storage management page loads
- [ ] Storage status shows correct strategy
- [ ] Small files upload and show correct storage location
- [ ] Large files upload to S3 (hybrid/s3_primary)
- [ ] Shared download links work
- [ ] AI chat works with uploaded datasets
- [ ] Migration between strategies works
- [ ] Storage verification passes
- [ ] MindsDB integration remains functional

## 🔄 Switching Between Strategies

You can change strategies anytime:

1. **Stop backend**: `Ctrl+C`
2. **Edit `.env`**: Change `STORAGE_STRATEGY`
3. **Restart backend**: `python -m uvicorn main:app --reload`
4. **Check status**: Visit `/admin/storage`
5. **Migrate files**: Use migration tools if needed

## 📈 Performance Testing

### Upload Performance
- Test upload speeds with different strategies
- Compare local vs S3 upload times
- Check network impact

### Download Performance  
- Test shared download speeds
- Compare direct S3 URLs vs local streaming
- Monitor bandwidth usage

### Storage Efficiency
- Check actual storage usage (local vs S3)
- Monitor costs for S3 storage
- Verify file deduplication

## 🎯 Next Steps

After testing, you can:
1. **Set production strategy** based on testing results
2. **Configure MindsDB** to use the same storage
3. **Set up monitoring** for storage health
4. **Implement backup policies** for redundant strategy
5. **Scale up** with additional S3 buckets if needed

## 📞 Support

If you encounter issues:
1. Check the storage management page for diagnostics
2. Review backend logs for detailed errors
3. Use storage verification to check file integrity
4. Check MindsDB compatibility with chosen strategy

Your system is now ready for comprehensive dual storage testing! 🚀