#!/usr/bin/env python3
"""
Test the validation fix for dataset 35
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.dataset import Dataset
from app.services.storage import StorageService

def test_validation_fix():
    """Test the validation fix for dataset 35."""
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("Testing validation fix for dataset 35...")
        
        # Get dataset 35
        dataset = db.query(Dataset).filter(Dataset.id == 35).first()
        
        if not dataset:
            print("❌ Dataset 35 not found")
            return
        
        print(f"Dataset: {dataset.name}")
        print(f"File path: {dataset.file_path}")
        print(f"Public share enabled: {dataset.public_share_enabled}")
        print(f"Share token: {dataset.share_token}")
        
        # Test storage service validation
        try:
            storage_service = StorageService()
            if hasattr(storage_service, 'backend') and hasattr(storage_service.backend, 'storage_dir'):
                storage_base = storage_service.backend.storage_dir
            else:
                storage_base = os.path.abspath(settings.STORAGE_BASE_PATH)
            
            full_path = os.path.join(storage_base, dataset.file_path)
            file_exists = os.path.exists(full_path)
            
            print(f"Storage base: {storage_base}")
            print(f"Full path: {full_path}")
            print(f"File exists: {file_exists}")
            
            if file_exists:
                print("✅ File validation should now pass")
            else:
                print("❌ File still not found - validation may still fail")
                
        except Exception as e:
            print(f"❌ Storage service error: {e}")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_validation_fix()