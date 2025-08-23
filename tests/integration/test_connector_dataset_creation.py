#!/usr/bin/env python3
"""
Test script to create API dataset via connector API endpoint
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.dataset import Dataset, DatabaseConnector
from app.models.user import User
from app.api.data_connectors import _create_api_dataset_fallback
from pydantic import BaseModel

# Database URL
DATABASE_URL = "sqlite:////Users/syaikhipin/Documents/program/simpleaisharing/storage/aishare_platform.db"

class CreateDatasetFromConnector(BaseModel):
    dataset_name: str
    description: str = ""
    table_or_endpoint: str = ""
    sharing_level: str = "private"

async def test_api_dataset_creation():
    """Test creating API dataset using the backend function"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get a successful API connector
        connector = db.query(DatabaseConnector).filter(
            DatabaseConnector.connector_type == "api",
            DatabaseConnector.test_status == "success"
        ).first()
        
        if not connector:
            print("❌ No successful API connector found")
            return
        
        # Get user
        user = db.query(User).filter(User.is_active == True).first()
        
        print(f"🧪 Testing API dataset creation")
        print(f"📡 Connector: {connector.name}")
        print(f"🔗 API: {connector.connection_config['base_url']}{connector.connection_config.get('endpoint', '')}")
        
        # Create dataset data
        dataset_data = CreateDatasetFromConnector(
            dataset_name=f"Test Enhanced API Dataset {int(asyncio.get_event_loop().time())}",
            description="Test dataset created with enhanced metadata from API connector",
            table_or_endpoint="",  # Use connector's default endpoint
            sharing_level="organization"
        )
        
        # Test the fallback function (which has our enhanced metadata)
        result = await _create_api_dataset_fallback(connector, dataset_data, user.id)
        
        if result.get("success"):
            dataset_id = result["dataset_id"]
            print(f"✅ Created dataset successfully!")
            print(f"   Dataset ID: {dataset_id}")
            print(f"   Dataset Name: {result['dataset_name']}")
            print(f"   API Endpoint: {result['api_endpoint']}")
            print(f"   Data Count: {result['data_count']}")
            
            # Verify the metadata
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if dataset:
                print(f"\n📊 Metadata verification:")
                print(f"   • file_metadata: {'✅ Present' if dataset.file_metadata else '❌ Missing'}")
                print(f"   • schema_metadata: {'✅ Present' if dataset.schema_metadata else '❌ Missing'}")
                print(f"   • quality_metrics: {'✅ Present' if dataset.quality_metrics else '❌ Missing'}")
                print(f"   • preview_data: {'✅ Present' if dataset.preview_data else '❌ Missing'}")
                print(f"   • column_statistics: {'✅ Present' if dataset.column_statistics else '❌ Missing'}")
                
                if dataset.file_metadata:
                    print(f"   • API URL: {dataset.file_metadata.get('api_url')}")
                    print(f"   • Total records: {dataset.file_metadata.get('total_records')}")
                    print(f"   • Data keys: {dataset.file_metadata.get('data_keys')}")
            
            return dataset_id
        else:
            print(f"❌ Dataset creation failed: {result.get('error')}")
            return None
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        db.close()

def check_all_api_datasets():
    """Check metadata status of all API datasets"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("\n🔍 Checking all API datasets:")
        
        api_datasets = db.query(Dataset).filter(
            Dataset.type == "api"
        ).order_by(Dataset.created_at.desc()).limit(10).all()
        
        for dataset in api_datasets:
            print(f"\n📁 {dataset.name} (ID: {dataset.id})")
            print(f"   Created: {dataset.created_at}")
            print(f"   Rows: {dataset.row_count}")
            print(f"   Columns: {dataset.column_count}")
            
            metadata_status = []
            if dataset.file_metadata:
                metadata_status.append("file_metadata ✅")
            else:
                metadata_status.append("file_metadata ❌")
                
            if dataset.schema_metadata:
                metadata_status.append("schema_metadata ✅")
            else:
                metadata_status.append("schema_metadata ❌")
                
            if dataset.quality_metrics:
                metadata_status.append("quality_metrics ✅")
            else:
                metadata_status.append("quality_metrics ❌")
                
            if dataset.preview_data:
                metadata_status.append("preview_data ✅")
            else:
                metadata_status.append("preview_data ❌")
            
            print(f"   Metadata: {', '.join(metadata_status)}")
        
    finally:
        db.close()

async def main():
    """Main test function"""
    print("🧪 API Dataset Enhanced Metadata Test\n")
    
    # Check current status
    check_all_api_datasets()
    
    # Create new dataset with enhanced metadata
    print("\n🔨 Creating new API dataset...")
    dataset_id = await test_api_dataset_creation()
    
    if dataset_id:
        print(f"\n✅ Test completed successfully!")
        print(f"💡 New dataset ID: {dataset_id}")
        print(f"🎯 Frontend should now display enhanced metadata for this dataset")
    else:
        print("\n❌ Test failed")

if __name__ == "__main__":
    asyncio.run(main())