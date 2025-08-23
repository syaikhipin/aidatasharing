#!/usr/bin/env python3
"""
Debug script to check file metadata storage in database
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.dataset import Dataset
from app.core.database import Base
import json

# Database URL - update as needed
DATABASE_URL = "sqlite:////Users/syaikhipin/Documents/program/simpleaisharing/storage/aishare_platform.db"

def check_file_metadata():
    """Check if file_metadata is being stored properly"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("🔍 Checking file metadata storage...")
        
        # Get recent datasets (including deleted ones to see all data)
        datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).limit(10).all()
        
        if not datasets:
            print("❌ No datasets found")
            return
        
        print(f"📊 Found {len(datasets)} datasets")
        
        for dataset in datasets:
            print(f"\n📁 Dataset: {dataset.name} (ID: {dataset.id})")
            print(f"   Type: {dataset.type}")
            print(f"   Created: {dataset.created_at}")
            
            # Check file_metadata
            if dataset.file_metadata:
                print(f"   ✅ file_metadata: {len(str(dataset.file_metadata))} chars")
                if isinstance(dataset.file_metadata, dict):
                    print(f"      Keys: {list(dataset.file_metadata.keys())}")
                else:
                    print(f"      Type: {type(dataset.file_metadata)}")
            else:
                print(f"   ❌ file_metadata: Empty/None")
            
            # Check preview_data
            if dataset.preview_data:
                print(f"   ✅ preview_data: {len(str(dataset.preview_data))} chars")
                if isinstance(dataset.preview_data, dict):
                    print(f"      Keys: {list(dataset.preview_data.keys())}")
                else:
                    print(f"      Type: {type(dataset.preview_data)}")
            else:
                print(f"   ❌ preview_data: Empty/None")
            
            # Check schema_metadata
            if dataset.schema_metadata:
                print(f"   ✅ schema_metadata: {len(str(dataset.schema_metadata))} chars")
                if isinstance(dataset.schema_metadata, dict):
                    print(f"      Keys: {list(dataset.schema_metadata.keys())}")
                else:
                    print(f"      Type: {type(dataset.schema_metadata)}")
            else:
                print(f"   ❌ schema_metadata: Empty/None")
            
            # Check quality_metrics
            if dataset.quality_metrics:
                print(f"   ✅ quality_metrics: {len(str(dataset.quality_metrics))} chars")
                if isinstance(dataset.quality_metrics, dict):
                    print(f"      Keys: {list(dataset.quality_metrics.keys())}")
                else:
                    print(f"      Type: {type(dataset.quality_metrics)}")
            else:
                print(f"   ❌ quality_metrics: Empty/None")
            
            # Check basic metadata
            print(f"   Row count: {dataset.row_count}")
            print(f"   Column count: {dataset.column_count}")
            print(f"   Size bytes: {dataset.size_bytes}")
            print(f"   File path: {dataset.file_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    check_file_metadata()