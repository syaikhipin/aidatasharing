#!/usr/bin/env python3
"""
Test script to verify automatic chat setup functionality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.dataset import Dataset
from app.services.mindsdb import MindsDBService

def test_auto_chat_setup():
    """Test automatic chat setup for file datasets."""
    
    # Setup database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Find datasets that have file_upload records and might need setup
        from app.models.file_handler import FileUpload
        
        # Get datasets that have file_upload records
        datasets_with_uploads = db.query(Dataset).join(FileUpload, Dataset.id == FileUpload.dataset_id).limit(3).all()
        
        datasets = datasets_with_uploads
        print(f"Found {len(datasets)} file datasets to test")
        
        for dataset in datasets:
            print(f"\n{'='*50}")
            print(f"Testing Dataset {dataset.id}: {dataset.name}")
            print(f"File path: {dataset.file_path}")
            print(f"AI processing status: {dataset.ai_processing_status}")
            print(f"MindsDB table: {dataset.mindsdb_table_name}")
            print(f"Chat enabled: {getattr(dataset, 'ai_chat_enabled', False)}")
            
            # Initialize MindsDB service
            mindsdb_service = MindsDBService()
            
            # Try to simulate a chat request (this should trigger auto setup if needed)
            try:
                print(f"🧪 Testing chat functionality for dataset {dataset.id}")
                response = mindsdb_service.chat_with_dataset(
                    dataset_id=str(dataset.id),
                    message="Tell me about this dataset",
                    user_id=1  # Mock user ID
                )
                
                print(f"✅ Chat test completed for dataset {dataset.id}")
                print(f"Response keys: {list(response.keys())}")
                
                if response.get("error"):
                    print(f"⚠️ Chat error: {response.get('error')}")
                else:
                    print(f"✅ Chat response received: {response.get('answer', 'No answer')[:100]}...")
                
            except Exception as e:
                print(f"❌ Chat test failed for dataset {dataset.id}: {e}")
            
            # Refresh dataset to check if auto setup happened
            db.refresh(dataset)
            print(f"📊 After test - AI status: {dataset.ai_processing_status}")
            print(f"📊 After test - MindsDB table: {dataset.mindsdb_table_name}")
            print(f"📊 After test - Chat enabled: {getattr(dataset, 'ai_chat_enabled', False)}")
            
        print(f"\n✅ Auto chat setup test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Testing automatic chat setup functionality...")
    test_auto_chat_setup()