#!/usr/bin/env python3
"""
Script to create missing database connectors for uploaded file datasets.
This script will identify uploaded file datasets that don't have proper MindsDB database connectors
and create them to make the datasets accessible for AI chat functionality.
"""

import os
import sys
import logging
from datetime import datetime

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_app_dir = os.path.join(backend_dir, 'backend')
sys.path.insert(0, backend_app_dir)

from app.core.database import get_db
from app.models.dataset import Dataset
from app.models.file_handler import FileUpload
from app.services.mindsdb import mindsdb_service
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_missing_database_connectors():
    """Create database connectors for uploaded file datasets that don't have them."""
    try:
        logger.info("🔍 Starting database connector creation for uploaded file datasets...")
        
        # Get database session
        db = next(get_db())
        
        # Find all datasets that are not web connectors (uploaded files)
        uploaded_datasets = db.query(Dataset).filter(
            Dataset.connector_id.is_(None),
            Dataset.source_url.is_(None)
        ).all()
        
        logger.info(f"📊 Found {len(uploaded_datasets)} uploaded file datasets")
        
        created_count = 0
        failed_count = 0
        already_exists_count = 0
        
        for dataset in uploaded_datasets:
            logger.info(f"🔄 Processing dataset: {dataset.name} (ID: {dataset.id})")
            
            # Find the associated file upload
            file_upload = db.query(FileUpload).filter(
                FileUpload.dataset_id == dataset.id
            ).first()
            
            if not file_upload:
                logger.warning(f"⚠️ No file upload record found for dataset {dataset.id}")
                failed_count += 1
                continue
            
            logger.info(f"📁 Found file: {file_upload.original_filename}")
            
            # Check if file exists
            if not os.path.exists(file_upload.file_path):
                logger.warning(f"⚠️ File not found: {file_upload.file_path}")
                failed_count += 1
                continue
            
            # Create database connector
            result = mindsdb_service.create_file_database_connector(file_upload)
            
            if result.get("success"):
                if "already exists" in result.get("message", "").lower():
                    logger.info(f"✅ Database connector already exists for {file_upload.original_filename}")
                    already_exists_count += 1
                else:
                    logger.info(f"✅ Created database connector for {file_upload.original_filename}")
                    created_count += 1
                
                # Log test result
                test_result = result.get("test_result", {})
                if test_result.get("success"):
                    logger.info(f"📊 Test successful - {test_result.get('rows_retrieved', 0)} rows, {len(test_result.get('columns', []))} columns")
                else:
                    logger.warning(f"⚠️ Test failed: {test_result.get('error', 'Unknown error')}")
            else:
                logger.error(f"❌ Failed to create database connector for {file_upload.original_filename}: {result.get('error')}")
                failed_count += 1
        
        # Summary
        logger.info(f"📈 Summary:")
        logger.info(f"  - Created: {created_count}")
        logger.info(f"  - Already existed: {already_exists_count}")
        logger.info(f"  - Failed: {failed_count}")
        logger.info(f"  - Total processed: {len(uploaded_datasets)}")
        
        return {
            "total_datasets": len(uploaded_datasets),
            "created": created_count,
            "already_exists": already_exists_count,
            "failed": failed_count,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"❌ Script failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def test_database_connectors():
    """Test existing database connectors to verify they work."""
    try:
        logger.info("🧪 Testing existing database connectors...")
        
        # Get database session
        db = next(get_db())
        
        # Find all uploaded file datasets
        uploaded_datasets = db.query(Dataset).filter(
            Dataset.connector_id.is_(None),
            Dataset.source_url.is_(None)
        ).all()
        
        working_count = 0
        broken_count = 0
        
        for dataset in uploaded_datasets:
            file_upload = db.query(FileUpload).filter(
                FileUpload.dataset_id == dataset.id
            ).first()
            
            if not file_upload:
                continue
            
            database_name = f"file_db_{file_upload.id}"
            
            # Test the database connector
            test_result = mindsdb_service.test_file_database_connector(database_name, file_upload)
            
            if test_result.get("success"):
                logger.info(f"✅ {file_upload.original_filename}: Working ({test_result.get('rows_retrieved', 0)} rows)")
                working_count += 1
            else:
                logger.warning(f"❌ {file_upload.original_filename}: Failed - {test_result.get('error', 'Unknown error')}")
                broken_count += 1
        
        logger.info(f"🧪 Test Summary:")
        logger.info(f"  - Working: {working_count}")
        logger.info(f"  - Broken: {broken_count}")
        
        return {
            "working": working_count,
            "broken": broken_count,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Main function to run the database connector creation and testing."""
    logger.info("🚀 Starting MindsDB database connector creation and testing...")
    
    # Create missing database connectors
    creation_result = create_missing_database_connectors()
    
    if not creation_result.get("success"):
        logger.error(f"❌ Database connector creation failed: {creation_result.get('error')}")
        return
    
    # Test the database connectors
    test_result = test_database_connectors()
    
    if not test_result.get("success"):
        logger.error(f"❌ Database connector testing failed: {test_result.get('error')}")
        return
    
    logger.info("🎉 Database connector creation and testing completed successfully!")
    
    # Final summary
    logger.info("📋 Final Summary:")
    logger.info(f"  - Total datasets processed: {creation_result.get('total_datasets', 0)}")
    logger.info(f"  - New connectors created: {creation_result.get('created', 0)}")
    logger.info(f"  - Connectors already existed: {creation_result.get('already_exists', 0)}")
    logger.info(f"  - Creation failures: {creation_result.get('failed', 0)}")
    logger.info(f"  - Working connectors: {test_result.get('working', 0)}")
    logger.info(f"  - Broken connectors: {test_result.get('broken', 0)}")

if __name__ == "__main__":
    main()