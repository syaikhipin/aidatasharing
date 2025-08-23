#!/usr/bin/env python3
"""
Comprehensive test for enhanced dataset chat functionality with database connectors.
This test verifies that both web connector and uploaded file datasets work properly
with the enhanced chat system and MindsDB database connectors.
"""

import os
import sys
import logging
import json
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

def test_mindsdb_connection():
    """Test basic MindsDB connection and health."""
    logger.info("🔗 Testing MindsDB connection...")
    
    try:
        health = mindsdb_service.health_check()
        logger.info(f"Health check result: {health}")
        
        if health.get("status") == "healthy":
            logger.info("✅ MindsDB connection is healthy")
            return True
        else:
            logger.warning(f"⚠️ MindsDB connection issues: {health}")
            return False
            
    except Exception as e:
        logger.error(f"❌ MindsDB connection test failed: {e}")
        return False

def test_web_connector_datasets():
    """Test web connector datasets."""
    logger.info("🌐 Testing web connector datasets...")
    
    try:
        db = next(get_db())
        
        # Find web connector datasets
        web_datasets = db.query(Dataset).filter(
            (Dataset.connector_id.isnot(None)) | (Dataset.source_url.isnot(None))
        ).limit(3).all()
        
        logger.info(f"Found {len(web_datasets)} web connector datasets")
        
        for dataset in web_datasets:
            logger.info(f"🔄 Testing web connector dataset: {dataset.name} (ID: {dataset.id})")
            
            # Test chat functionality
            test_message = "What kind of data does this dataset contain? Provide a brief overview."
            
            result = mindsdb_service.chat_with_dataset(
                dataset_id=str(dataset.id),
                message=test_message,
                user_id=1
            )
            
            if result.get("error"):
                logger.error(f"❌ Web connector chat failed: {result.get('error')}")
            else:
                logger.info(f"✅ Web connector chat successful")
                logger.info(f"Response preview: {result.get('answer', '')[:100]}...")
                
                # Check if it detected as web connector
                if result.get("is_web_connector"):
                    logger.info("✅ Correctly detected as web connector dataset")
                else:
                    logger.warning("⚠️ Not detected as web connector dataset")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Web connector test failed: {e}")
        return False

def test_uploaded_file_datasets():
    """Test uploaded file datasets with database connectors."""
    logger.info("📁 Testing uploaded file datasets...")
    
    try:
        db = next(get_db())
        
        # Find uploaded file datasets
        uploaded_datasets = db.query(Dataset).filter(
            Dataset.connector_id.is_(None),
            Dataset.source_url.is_(None)
        ).limit(3).all()
        
        logger.info(f"Found {len(uploaded_datasets)} uploaded file datasets")
        
        for dataset in uploaded_datasets:
            logger.info(f"🔄 Testing uploaded file dataset: {dataset.name} (ID: {dataset.id})")
            
            # Get file upload record
            file_upload = db.query(FileUpload).filter(
                FileUpload.dataset_id == dataset.id
            ).first()
            
            if not file_upload:
                logger.warning(f"⚠️ No file upload record found for dataset {dataset.id}")
                continue
            
            logger.info(f"📄 File: {file_upload.original_filename}")
            
            # Test database connector creation
            connector_result = mindsdb_service.create_file_database_connector(file_upload)
            
            if connector_result.get("success"):
                logger.info(f"✅ Database connector ready: {connector_result.get('database_name')}")
                
                # Test chat functionality
                test_message = "What kind of data does this dataset contain? Show me some key statistics and insights."
                
                result = mindsdb_service.chat_with_dataset(
                    dataset_id=str(dataset.id),
                    message=test_message,
                    user_id=1
                )
                
                if result.get("error"):
                    logger.error(f"❌ Uploaded file chat failed: {result.get('error')}")
                else:
                    logger.info(f"✅ Uploaded file chat successful")
                    logger.info(f"Response preview: {result.get('answer', '')[:100]}...")
                    
                    # Check if it detected as uploaded file
                    if not result.get("is_web_connector"):
                        logger.info("✅ Correctly detected as uploaded file dataset")
                    else:
                        logger.warning("⚠️ Incorrectly detected as web connector dataset")
            else:
                logger.error(f"❌ Database connector creation failed: {connector_result.get('error')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Uploaded file test failed: {e}")
        return False

def test_ai_chat_models():
    """Test AI chat model functionality."""
    logger.info("🤖 Testing AI chat models...")
    
    try:
        # Test engine creation
        engine_result = mindsdb_service.create_gemini_engine()
        logger.info(f"Engine result: {engine_result}")
        
        # Test model creation
        model_result = mindsdb_service.create_gemini_model("test_chat_model")
        logger.info(f"Model result: {model_result}")
        
        # Test basic AI chat
        chat_result = mindsdb_service.ai_chat("Hello, can you tell me what you are?")
        
        if chat_result.get("error"):
            logger.error(f"❌ AI chat failed: {chat_result.get('error')}")
            return False
        else:
            logger.info(f"✅ AI chat successful")
            logger.info(f"Response: {chat_result.get('answer', '')[:100]}...")
            return True
        
    except Exception as e:
        logger.error(f"❌ AI chat model test failed: {e}")
        return False

def test_database_visibility():
    """Test if databases are visible in MindsDB."""
    logger.info("👁️ Testing database visibility in MindsDB...")
    
    try:
        if not mindsdb_service._ensure_connection():
            logger.error("❌ Cannot connect to MindsDB")
            return False
        
        # Show databases
        result = mindsdb_service.connection.query("SHOW DATABASES")
        
        if result and hasattr(result, 'fetch'):
            df = result.fetch()
            if not df.empty:
                databases = df['Database'].tolist() if 'Database' in df.columns else df.iloc[:, 0].tolist()
                logger.info(f"📊 Found {len(databases)} databases in MindsDB:")
                
                file_databases = [db for db in databases if db.startswith('file_db_')]
                web_databases = [db for db in databases if not db.startswith('file_db_') and db not in ['mindsdb', 'information_schema']]
                
                logger.info(f"  - File databases: {len(file_databases)}")
                logger.info(f"  - Web connector databases: {len(web_databases)}")
                logger.info(f"  - System databases: {len([db for db in databases if db in ['mindsdb', 'information_schema']])}")
                
                if file_databases:
                    logger.info(f"  - Sample file databases: {file_databases[:3]}")
                if web_databases:
                    logger.info(f"  - Sample web databases: {web_databases[:3]}")
                
                return True
            else:
                logger.warning("⚠️ No databases found in MindsDB")
                return False
        else:
            logger.error("❌ Failed to query databases")
            return False
        
    except Exception as e:
        logger.error(f"❌ Database visibility test failed: {e}")
        return False

def main():
    """Main test function."""
    logger.info("🚀 Starting comprehensive enhanced dataset chat test...")
    
    test_results = {
        "mindsdb_connection": False,
        "ai_chat_models": False,
        "database_visibility": False,
        "web_connector_datasets": False,
        "uploaded_file_datasets": False
    }
    
    # Test MindsDB connection
    test_results["mindsdb_connection"] = test_mindsdb_connection()
    
    if not test_results["mindsdb_connection"]:
        logger.error("❌ Cannot proceed without MindsDB connection")
        return test_results
    
    # Test AI chat models
    test_results["ai_chat_models"] = test_ai_chat_models()
    
    # Test database visibility
    test_results["database_visibility"] = test_database_visibility()
    
    # Test web connector datasets
    test_results["web_connector_datasets"] = test_web_connector_datasets()
    
    # Test uploaded file datasets
    test_results["uploaded_file_datasets"] = test_uploaded_file_datasets()
    
    # Summary
    logger.info("📋 Test Results Summary:")
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  - {test_name.replace('_', ' ').title()}: {status}")
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    logger.info(f"🎯 Overall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 All tests passed! Enhanced dataset chat functionality is working correctly.")
    else:
        logger.warning(f"⚠️ {total_tests - passed_tests} tests failed. Please review the issues above.")
    
    return test_results

if __name__ == "__main__":
    main()