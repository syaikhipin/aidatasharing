#!/usr/bin/env python3
"""
Test script to validate the complete storage flow for both local and S3 storage.
This script tests file upload, download, and chat functionality.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_storage_service():
    """Test the storage service with both local and S3 backends"""
    from app.services.storage import storage_service
    
    # Check current backend
    backend_info = storage_service.get_backend_info()
    logger.info(f"✅ Storage Backend: {backend_info}")
    
    # Test storing a file
    test_content = b"Test,Data\nValue1,Value2\nValue3,Value4"
    test_filename = "test_dataset.csv"
    
    try:
        result = await storage_service.store_dataset_file(
            file_content=test_content,
            original_filename=test_filename,
            dataset_id=1,
            organization_id=1
        )
        logger.info(f"✅ File stored successfully: {result}")
        
        # Test retrieving the file
        file_path = result.get('relative_path')
        if file_path:
            content = await storage_service.retrieve_dataset_file(file_path)
            if content:
                logger.info(f"✅ File retrieved successfully: {len(content)} bytes")
            else:
                logger.error("❌ Failed to retrieve file")
                
            # Test getting file stream
            try:
                stream = await storage_service.get_dataset_file_stream(file_path)
                logger.info(f"✅ File stream created successfully")
            except Exception as e:
                logger.error(f"❌ Failed to create file stream: {e}")
                
            # Test getting file URL (for S3)
            if backend_info.get('supports_presigned_urls'):
                url = storage_service.get_dataset_file_url(file_path)
                if url:
                    logger.info(f"✅ Presigned URL generated: {url[:50]}...")
                else:
                    logger.warning("⚠️ Failed to generate presigned URL")
            else:
                logger.info("ℹ️ Backend does not support presigned URLs")
                
    except Exception as e:
        logger.error(f"❌ Storage test failed: {e}")
        

async def test_download_endpoint():
    """Test the download endpoint with unified storage"""
    logger.info("\n--- Testing Download Endpoint ---")
    
    # This would normally be called through an HTTP request
    # Here we simulate the key parts
    from app.services.storage import storage_service
    
    # Test with a mock file path
    test_paths = [
        "org_1/dataset_1_20240101_120000_abc123.csv",  # S3 style path
        "storage/test_file.csv",  # Local style path
    ]
    
    for test_path in test_paths:
        try:
            logger.info(f"Testing download for: {test_path}")
            
            # Check if we can get a stream
            if os.path.exists(test_path):
                # Local file exists
                logger.info(f"✅ Local file found: {test_path}")
            else:
                # Try through storage service
                try:
                    stream = await storage_service.get_dataset_file_stream(test_path)
                    logger.info(f"✅ Storage service can stream: {test_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Cannot stream {test_path}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Download test failed for {test_path}: {e}")


async def test_mindsdb_s3_integration():
    """Test MindsDB S3 connector for chat functionality"""
    logger.info("\n--- Testing MindsDB S3 Integration ---")
    
    try:
        from app.services.mindsdb import MindsDBService
        from app.services.storage import storage_service
        
        mindsdb = MindsDBService()
        backend_info = storage_service.get_backend_info()
        
        if backend_info.get("backend_type") == "S3StorageBackend":
            logger.info("✅ S3 backend detected, testing MindsDB S3 connector")
            
            # Test creating S3 connector
            import os
            s3_bucket = os.getenv('S3_BUCKET_NAME')
            s3_access_key = os.getenv('S3_ACCESS_KEY_ID')
            s3_secret_key = os.getenv('S3_SECRET_ACCESS_KEY')
            s3_endpoint = os.getenv('S3_ENDPOINT_URL')
            s3_region = os.getenv('S3_REGION', 'us-east-1')
            
            if all([s3_bucket, s3_access_key, s3_secret_key]):
                result = mindsdb.create_s3_connector(
                    connector_name="test_s3_connector",
                    bucket_name=s3_bucket,
                    access_key=s3_access_key,
                    secret_key=s3_secret_key,
                    endpoint_url=s3_endpoint,
                    region=s3_region
                )
                
                if result.get("success"):
                    logger.info(f"✅ S3 connector created: {result}")
                    
                    # Test querying S3 file
                    test_file_path = "org_1/dataset_1_test.csv"
                    query_result = mindsdb.query_s3_file(
                        s3_connector_name="test_s3_connector",
                        file_path=test_file_path
                    )
                    
                    if query_result.get("status") == "success":
                        logger.info(f"✅ S3 file query successful: {query_result.get('row_count')} rows")
                    else:
                        logger.warning(f"⚠️ S3 file query failed: {query_result}")
                else:
                    logger.error(f"❌ Failed to create S3 connector: {result}")
            else:
                logger.warning("⚠️ S3 credentials not configured")
        else:
            logger.info("ℹ️ Local backend detected, S3 connector not needed")
            
    except Exception as e:
        logger.error(f"❌ MindsDB S3 integration test failed: {e}")


async def main():
    """Run all tests"""
    logger.info("🚀 Starting Storage Flow Tests")
    
    # Test storage service
    await test_storage_service()
    
    # Test download endpoint
    await test_download_endpoint()
    
    # Test MindsDB S3 integration
    await test_mindsdb_s3_integration()
    
    logger.info("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())