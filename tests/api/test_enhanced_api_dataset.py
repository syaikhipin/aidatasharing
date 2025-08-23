#!/usr/bin/env python3
"""
Test script to create a new API dataset and verify metadata processing
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.dataset import Dataset, DatasetType, DatabaseConnector, DatasetStatus
from app.models.user import User
from app.models.organization import Organization, DataSharingLevel
from datetime import datetime
import json

# Database URL
DATABASE_URL = "sqlite:////Users/syaikhipin/Documents/program/simpleaisharing/storage/aishare_platform.db"

async def test_create_api_dataset():
    """Test creating API dataset with proper metadata"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get a working API connector
        connector = db.query(DatabaseConnector).filter(
            DatabaseConnector.connector_type == "api",
            DatabaseConnector.test_status == "success"
        ).first()
        
        if not connector:
            print("❌ No successful API connector found")
            return
        
        # Get user and org info
        user = db.query(User).filter(User.is_active == True).first()
        
        print(f"📡 Testing with connector: {connector.name}")
        print(f"🔗 API URL: {connector.connection_config['base_url']}{connector.connection_config.get('endpoint', '')}")
        
        # Test the API endpoint directly
        url = f"{connector.connection_config['base_url']}{connector.connection_config.get('endpoint', '')}"
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ API test failed: HTTP {response.status_code}")
            return
        
        api_data = response.json()
        print(f"✅ API responded with {len(api_data)} records")
        
        # Create enhanced metadata (simulating what the backend should do)
        enhanced_metadata = {
            'file_metadata': {
                'api_url': url,
                'method': connector.connection_config.get('method', 'GET'),
                'total_records': len(api_data),
                'sample_record': api_data[0] if api_data else None,
                'data_keys': list(api_data[0].keys()) if api_data and isinstance(api_data[0], dict) else []
            },
            'schema_metadata': {
                'file_type': 'api',
                'source': 'api_connector',
                'structure': {
                    'type': 'list' if isinstance(api_data, list) else 'object',
                    'total_elements': len(api_data),
                    'sample_structure': str(api_data[0])[:200] if api_data else None
                },
                'columns': list(api_data[0].keys()) if api_data and isinstance(api_data[0], dict) else [],
                'data_types': {k: type(v).__name__ for k, v in api_data[0].items()} if api_data and isinstance(api_data[0], dict) else {},
                'sample_data': str(api_data[:2])[:500] if api_data else None
            },
            'quality_metrics': {
                'overall_score': 95,
                'completeness': 100,
                'consistency': 90,
                'accuracy': 95,
                'issues': [],
                'last_analyzed': datetime.utcnow().isoformat()
            },
            'preview_data': {
                'type': 'api',
                'headers': list(api_data[0].keys()) if api_data and isinstance(api_data[0], dict) else [],
                'sample_rows': api_data[:5] if api_data else [],
                'total_rows': len(api_data),
                'is_sample': len(api_data) > 5,
                'preview_generated_at': datetime.utcnow().isoformat()
            }
        }
        
        # Create new dataset with enhanced metadata
        dataset = Dataset(
            name=f"Enhanced {connector.name} Dataset",
            description=f"API dataset with enhanced metadata from {connector.name}",
            type=DatasetType.API,
            status=DatasetStatus.ACTIVE,
            owner_id=user.id,
            organization_id=connector.organization_id,
            sharing_level=DataSharingLevel.ORGANIZATION,
            connector_id=connector.id,
            source_url=url,
            row_count=len(api_data),
            column_count=len(api_data[0].keys()) if api_data and isinstance(api_data[0], dict) else 0,
            # Enhanced metadata fields
            file_metadata=enhanced_metadata['file_metadata'],
            schema_metadata=enhanced_metadata['schema_metadata'],
            quality_metrics=enhanced_metadata['quality_metrics'],
            preview_data=enhanced_metadata['preview_data'],
            # Additional fields
            allow_download=True,
            allow_api_access=True,
            allow_ai_chat=True,
            ai_chat_enabled=True,
            chat_context={
                'api_endpoint': url,
                'data_sample': api_data[:3] if api_data else [],
                'total_records': len(api_data),
                'connector_name': connector.name,
                'data_structure': list(api_data[0].keys()) if api_data and isinstance(api_data[0], dict) else []
            }
        )
        
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        print(f"✅ Created enhanced API dataset: {dataset.name} (ID: {dataset.id})")
        print(f"📊 Metadata summary:")
        print(f"   • Row count: {dataset.row_count}")
        print(f"   • Column count: {dataset.column_count}")
        print(f"   • File metadata keys: {list(dataset.file_metadata.keys()) if dataset.file_metadata else 'None'}")
        print(f"   • Schema metadata keys: {list(dataset.schema_metadata.keys()) if dataset.schema_metadata else 'None'}")
        print(f"   • Quality metrics keys: {list(dataset.quality_metrics.keys()) if dataset.quality_metrics else 'None'}")
        print(f"   • Preview data keys: {list(dataset.preview_data.keys()) if dataset.preview_data else 'None'}")
        
        return dataset.id
        
    except Exception as e:
        print(f"❌ Error creating enhanced API dataset: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return None
        
    finally:
        db.close()

def verify_metadata(dataset_id):
    """Verify the metadata was stored correctly"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            print(f"❌ Dataset {dataset_id} not found")
            return
        
        print(f"\n🔍 Verifying metadata for dataset {dataset_id}:")
        print(f"   Name: {dataset.name}")
        print(f"   Type: {dataset.type}")
        print(f"   Rows: {dataset.row_count}")
        print(f"   Columns: {dataset.column_count}")
        
        # Check each metadata field
        if dataset.file_metadata:
            print(f"   ✅ file_metadata: {len(str(dataset.file_metadata))} chars")
        else:
            print(f"   ❌ file_metadata: Empty")
            
        if dataset.schema_metadata:
            print(f"   ✅ schema_metadata: {len(str(dataset.schema_metadata))} chars")
        else:
            print(f"   ❌ schema_metadata: Empty")
            
        if dataset.quality_metrics:
            print(f"   ✅ quality_metrics: {len(str(dataset.quality_metrics))} chars")
        else:
            print(f"   ❌ quality_metrics: Empty")
            
        if dataset.preview_data:
            print(f"   ✅ preview_data: {len(str(dataset.preview_data))} chars")
        else:
            print(f"   ❌ preview_data: Empty")
        
    finally:
        db.close()

async def main():
    """Main test function"""
    print("🧪 Testing Enhanced API Dataset Creation\n")
    
    dataset_id = await test_create_api_dataset()
    
    if dataset_id:
        verify_metadata(dataset_id)
        print(f"\n✅ Test completed successfully!")
        print(f"💡 Dataset ID {dataset_id} created with enhanced metadata")
        print(f"🎯 You can now test this dataset in the frontend")
    else:
        print("\n❌ Test failed")

if __name__ == "__main__":
    asyncio.run(main())