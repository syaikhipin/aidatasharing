#!/usr/bin/env python3
"""
Create comprehensive demo data with real API connectors and datasets
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
import json
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.dataset import Dataset, DatasetType, DatabaseConnector, DatasetStatus
from app.models.user import User
from app.models.organization import Organization, DataSharingLevel
from datetime import datetime

# Database URL
DATABASE_URL = "sqlite:////Users/syaikhipin/Documents/program/simpleaisharing/storage/aishare_platform.db"

# Real API endpoints that provide useful demo data
DEMO_APIS = [
    {
        "name": "JSONPlaceholder Posts API",
        "description": "Sample blog posts data for testing and prototyping",
        "base_url": "https://jsonplaceholder.typicode.com",
        "endpoint": "/posts",
        "method": "GET",
        "expected_fields": ["userId", "id", "title", "body"],
        "demo_use_case": "Blog content management, social media analysis"
    },
    {
        "name": "JSONPlaceholder Users API", 
        "description": "Sample user profiles and contact information",
        "base_url": "https://jsonplaceholder.typicode.com",
        "endpoint": "/users",
        "method": "GET", 
        "expected_fields": ["id", "name", "username", "email", "phone", "website"],
        "demo_use_case": "Customer database, user management"
    },
    {
        "name": "Cat Facts API",
        "description": "Random cat facts for fun data analysis",
        "base_url": "https://catfact.ninja",
        "endpoint": "/facts?limit=50",
        "method": "GET",
        "expected_fields": ["fact", "length"],
        "demo_use_case": "Text analysis, content generation, fun data"
    },
    {
        "name": "Rick and Morty Characters",
        "description": "Character data from Rick and Morty series",
        "base_url": "https://rickandmortyapi.com",
        "endpoint": "/api/character",
        "method": "GET",
        "expected_fields": ["id", "name", "status", "species", "gender", "origin", "location"],
        "demo_use_case": "Entertainment data analysis, character analytics"
    }
]

def test_api_endpoints():
    """Test all demo APIs to ensure they work"""
    working_apis = []
    
    print("🔍 Testing demo API endpoints...")
    
    for api in DEMO_APIS:
        try:
            url = f"{api['base_url']}{api['endpoint']}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, dict) and 'data' in data:
                    # Rick and Morty API format
                    actual_data = data['data']
                    count = len(actual_data) if isinstance(actual_data, list) else 1
                elif isinstance(data, dict) and 'data' in data:
                    # Cat Facts API format  
                    actual_data = data['data']
                    count = len(actual_data) if isinstance(actual_data, list) else 1
                elif isinstance(data, list):
                    # Direct list format
                    actual_data = data
                    count = len(actual_data)
                else:
                    # Single object
                    actual_data = [data]
                    count = 1
                
                print(f"✅ {api['name']}: {count} records")
                api['test_data'] = actual_data[:3]  # Store first 3 for testing
                api['total_records'] = count
                api['working_url'] = url
                working_apis.append(api)
                
            else:
                print(f"❌ {api['name']}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {api['name']}: {e}")
    
    return working_apis

def create_demo_api_connectors(working_apis):
    """Create API connectors for working APIs"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    created_connectors = []
    
    try:
        # Get the first active user and org
        user = db.query(User).filter(User.is_active == True).first()
        org = db.query(Organization).filter(Organization.is_active == True).first()
        
        if not user or not org:
            print("❌ No active user or organization found")
            return []
        
        print(f"\n🔨 Creating API connectors for org '{org.name}'...")
        
        for api in working_apis:
            # Check if connector already exists
            existing = db.query(DatabaseConnector).filter(
                DatabaseConnector.name == api['name'],
                DatabaseConnector.organization_id == org.id
            ).first()
            
            if existing:
                print(f"⚠️ Connector '{api['name']}' already exists (ID: {existing.id})")
                created_connectors.append(existing)
                continue
            
            # Create new connector
            connector = DatabaseConnector(
                name=api['name'],
                connector_type="api",
                description=api['description'],
                organization_id=org.id,
                created_by=user.id,
                connection_config={
                    "base_url": api['base_url'],
                    "endpoint": api['endpoint'],
                    "method": api['method'],
                    "timeout": 30,
                    "headers": {}
                },
                credentials=None,  # These APIs don't need auth
                test_status="untested",
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            db.add(connector)
            db.flush()  # Get the ID
            
            print(f"✅ Created connector: {api['name']} (ID: {connector.id})")
            created_connectors.append(connector)
        
        db.commit()
        return created_connectors
        
    except Exception as e:
        print(f"❌ Error creating connectors: {e}")
        db.rollback()
        return []
        
    finally:
        db.close()

def create_demo_datasets(connectors, working_apis):
    """Create demo datasets from the connectors"""
    from app.api.data_connectors import _create_api_dataset_fallback
    from pydantic import BaseModel
    
    class CreateDatasetFromConnector(BaseModel):
        dataset_name: str
        description: str = ""
        table_or_endpoint: str = ""
        sharing_level: str = "organization"
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    created_datasets = []
    
    try:
        user = db.query(User).filter(User.is_active == True).first()
        
        print(f"\n📊 Creating demo datasets...")
        
        for i, connector in enumerate(connectors):
            api_info = working_apis[i] if i < len(working_apis) else working_apis[0]
            
            # Check if dataset already exists
            existing = db.query(Dataset).filter(
                Dataset.connector_id == connector.id,
                Dataset.name.like(f"%{connector.name}%Dataset%")
            ).first()
            
            if existing:
                print(f"⚠️ Dataset from '{connector.name}' already exists (ID: {existing.id})")
                created_datasets.append(existing)
                continue
            
            # Create dataset data
            dataset_data = CreateDatasetFromConnector(
                dataset_name=f"{connector.name} Dataset",
                description=f"Demo dataset from {connector.name} - {api_info['demo_use_case']}",
                table_or_endpoint="",  # Use connector's default
                sharing_level="organization"
            )
            
            # Create dataset using our enhanced fallback function
            async def create_dataset():
                return await _create_api_dataset_fallback(connector, dataset_data, user.id)
            
            # Run the async function
            result = asyncio.run(create_dataset())
            
            if result.get("success"):
                dataset_id = result["dataset_id"]
                dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
                
                print(f"✅ Created dataset: {dataset.name} (ID: {dataset_id})")
                print(f"   📈 Records: {result['data_count']}")
                print(f"   🔗 API: {result['api_endpoint']}")
                
                created_datasets.append(dataset)
            else:
                print(f"❌ Failed to create dataset from {connector.name}: {result.get('error')}")
        
        return created_datasets
        
    except Exception as e:
        print(f"❌ Error creating datasets: {e}")
        import traceback
        traceback.print_exc()
        return []
        
    finally:
        db.close()

def verify_demo_setup():
    """Verify the demo setup is complete"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print(f"\n🔍 Verifying demo setup...")
        
        # Count API connectors
        api_connectors = db.query(DatabaseConnector).filter(
            DatabaseConnector.connector_type == "api",
            DatabaseConnector.is_active == True
        ).all()
        
        # Count API datasets with metadata
        api_datasets = db.query(Dataset).filter(
            Dataset.type == "api",
            Dataset.file_metadata.isnot(None)
        ).all()
        
        print(f"📊 Demo Statistics:")
        print(f"   • API Connectors: {len(api_connectors)}")
        print(f"   • API Datasets with metadata: {len(api_datasets)}")
        
        print(f"\n📁 Recent API datasets:")
        for dataset in api_datasets[-5:]:  # Last 5
            metadata_count = sum([
                1 if dataset.file_metadata else 0,
                1 if dataset.schema_metadata else 0,
                1 if dataset.quality_metrics else 0,
                1 if dataset.preview_data else 0
            ])
            print(f"   • {dataset.name} - {dataset.row_count} rows - {metadata_count}/4 metadata fields")
        
        return len(api_connectors), len(api_datasets)
        
    finally:
        db.close()

async def main():
    """Main demo setup function"""
    print("🎯 Setting up comprehensive demo data with real APIs\n")
    
    # Test API endpoints
    working_apis = test_api_endpoints()
    
    if not working_apis:
        print("❌ No working APIs found. Cannot proceed.")
        return
    
    print(f"\n✅ Found {len(working_apis)} working APIs")
    
    # Create connectors
    connectors = create_demo_api_connectors(working_apis)
    
    if not connectors:
        print("❌ Failed to create connectors")
        return
    
    # Create datasets
    datasets = create_demo_datasets(connectors, working_apis)
    
    # Verify setup
    connector_count, dataset_count = verify_demo_setup()
    
    print(f"\n🎉 Demo setup complete!")
    print(f"✅ {connector_count} API connectors available")
    print(f"✅ {dataset_count} API datasets with enhanced metadata")
    print(f"\n💡 Next steps:")
    print(f"   • Open the frontend connections page")
    print(f"   • Test creating datasets from API connectors")
    print(f"   • Verify enhanced metadata displays correctly")
    print(f"   • Try AI chat with the API datasets")

if __name__ == "__main__":
    asyncio.run(main())