#!/usr/bin/env python3
"""
Test script to create API connector with real data and test dataset creation flow
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.dataset import Dataset, DatasetType, DatabaseConnector
from app.models.user import User
from app.models.organization import Organization
from datetime import datetime

# Database URL
DATABASE_URL = "sqlite:////Users/syaikhipin/Documents/program/simpleaisharing/storage/aishare_platform.db"

def test_api_endpoints():
    """Test real API endpoints to ensure they work"""
    apis_to_test = [
        {
            "name": "JSONPlaceholder Posts",
            "base_url": "https://jsonplaceholder.typicode.com",
            "endpoint": "/posts",
            "description": "Free fake API for testing and prototyping - Posts data"
        },
        {
            "name": "JSONPlaceholder Users", 
            "base_url": "https://jsonplaceholder.typicode.com",
            "endpoint": "/users",
            "description": "Free fake API for testing and prototyping - Users data"
        },
        {
            "name": "Cat Facts API",
            "base_url": "https://catfact.ninja",
            "endpoint": "/facts",
            "description": "Random cat facts API"
        },
        {
            "name": "REST Countries",
            "base_url": "https://restcountries.com",
            "endpoint": "/v3.1/all",
            "description": "Countries data with detailed information"
        }
    ]
    
    working_apis = []
    
    print("🔍 Testing API endpoints...")
    
    for api in apis_to_test:
        try:
            url = f"{api['base_url']}{api['endpoint']}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    count = len(data)
                    print(f"✅ {api['name']}: {count} records")
                    api['sample_data'] = data[:3]  # First 3 records
                    api['total_records'] = count
                    working_apis.append(api)
                elif isinstance(data, dict):
                    print(f"✅ {api['name']}: Object data")
                    api['sample_data'] = [data]
                    api['total_records'] = 1
                    working_apis.append(api)
                else:
                    print(f"⚠️ {api['name']}: Unexpected data format")
            else:
                print(f"❌ {api['name']}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {api['name']}: {e}")
    
    return working_apis

def check_existing_data():
    """Check existing connectors and datasets"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("\n🔍 Checking existing data...")
        
        # Check API connectors
        api_connectors = db.query(DatabaseConnector).filter(
            DatabaseConnector.connector_type == "api"
        ).all()
        
        print(f"📊 Found {len(api_connectors)} API connectors:")
        for connector in api_connectors:
            datasets = db.query(Dataset).filter(Dataset.connector_id == connector.id).all()
            print(f"   • {connector.name} (ID: {connector.id}) - Test: {connector.test_status} - Datasets: {len(datasets)}")
            
            for dataset in datasets:
                print(f"     → Dataset: {dataset.name} (ID: {dataset.id}) - Rows: {dataset.row_count}")
        
        # Check users and organizations
        users = db.query(User).filter(User.is_active == True).all()
        orgs = db.query(Organization).filter(Organization.is_active == True).all()
        
        print(f"\n👥 Active users: {len(users)}")
        for user in users[:3]:  # Show first 3
            print(f"   • {user.full_name} ({user.email}) - Org: {user.organization_id}")
            
        print(f"🏢 Active organizations: {len(orgs)}")
        for org in orgs:
            print(f"   • {org.name} (ID: {org.id})")
        
        return {
            'connectors': api_connectors,
            'users': users,
            'organizations': orgs
        }
        
    finally:
        db.close()

def create_demo_api_connector():
    """Create a new API connector with working API for demo"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get the first active user and org
        user = db.query(User).filter(User.is_active == True).first()
        org = db.query(Organization).filter(Organization.is_active == True).first()
        
        if not user or not org:
            print("❌ No active user or organization found")
            return None
        
        # Create new API connector with JSONPlaceholder
        connector = DatabaseConnector(
            name="Demo JSONPlaceholder API",
            connector_type="api",
            description="Demo API connector with real JSONPlaceholder data for testing",
            organization_id=org.id,
            created_by=user.id,
            connection_config={
                "base_url": "https://jsonplaceholder.typicode.com",
                "endpoint": "/posts",
                "method": "GET",
                "timeout": 30,
                "headers": {}
            },
            credentials=None,  # No auth needed for JSONPlaceholder
            test_status="untested",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(connector)
        db.commit()
        db.refresh(connector)
        
        print(f"✅ Created demo API connector: {connector.name} (ID: {connector.id})")
        return connector
        
    except Exception as e:
        print(f"❌ Error creating connector: {e}")
        db.rollback()
        return None
        
    finally:
        db.close()

def main():
    """Main test function"""
    print("🧪 API Connector and Dataset Creation Test\n")
    
    # Test API endpoints
    working_apis = test_api_endpoints()
    
    if not working_apis:
        print("❌ No working APIs found. Cannot proceed.")
        return
    
    print(f"\n✅ Found {len(working_apis)} working APIs")
    
    # Check existing data
    existing_data = check_existing_data()
    
    # Create demo connector if needed
    if len(existing_data['connectors']) < 3:
        print("\n🔨 Creating demo API connector...")
        demo_connector = create_demo_api_connector()
        if demo_connector:
            print("✅ Demo connector created successfully")
    
    print("\n📋 Summary:")
    print("• API endpoints tested and working")
    print("• Database has existing connectors and datasets")
    print("• Demo data is ready for frontend testing")
    print("\n💡 Next steps:")
    print("• Test the frontend connections page")
    print("• Try creating datasets from API connectors")
    print("• Verify dataset metadata display")

if __name__ == "__main__":
    main()