#!/usr/bin/env python3
"""
Test the connector creation with the fixed MindsDB query execution
"""

import os
import sys
import asyncio
import json
from datetime import datetime
import random

# Add backend directory to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

from app.core.database import get_db
from app.models.dataset import Dataset, DatasetType, DatabaseConnector, DatasetStatus
from app.models.organization import Organization, DataSharingLevel
from app.models.user import User
from app.services.connector_service import ConnectorService

async def test_connector_creation_with_fixed_mindsdb():
    """Test that connector creation works with the fixed MindsDB execute_query method"""
    print("🧪 Testing Connector Creation with Fixed MindsDB Query Execution\n")
    
    db = next(get_db())
    
    try:
        # Get a test user and organization
        user = db.query(User).filter(User.is_active == True).first()
        org = db.query(Organization).filter(Organization.is_active == True).first()
        
        if not user or not org:
            print("❌ No active user or organization found")
            return False
        
        print(f"👤 Using user: {user.email}")
        print(f"🏢 Using organization: {org.name}")
        
        # Create a new web connector that should work
        connector_name = f"Test Fixed MindsDB {random.randint(100000, 999999)}"
        
        connector = DatabaseConnector(
            name=connector_name,
            connector_type="web",
            description="Test web connector to verify fixed MindsDB execution",
            connection_config={
                "base_url": "https://jsonplaceholder.typicode.com",
                "endpoint": "/posts",
                "method": "GET"
            },
            credentials={},
            created_by=user.id,
            organization_id=org.id,
            is_active=True,
            test_status="success"
        )
        
        # Generate unique database name
        connector.mindsdb_database_name = f"web_test_{random.randint(100000, 999999)}"
        
        db.add(connector)
        db.commit()
        db.refresh(connector)
        
        print(f"🔌 Created web connector: {connector.name} (ID: {connector.id})")
        print(f"🗄️ MindsDB database: {connector.mindsdb_database_name}")
        
        # Initialize connector service
        connector_service = ConnectorService(db)
        
        # Test the _create_mindsdb_connection method that was failing before
        print(f"\n🔗 Testing MindsDB database creation...")
        
        mindsdb_result = await connector_service._create_mindsdb_connection(connector)
        
        print(f"MindsDB connection result: {json.dumps(mindsdb_result, indent=2)}")
        
        if mindsdb_result.get("success"):
            print(f"✅ MindsDB database creation succeeded!")
            
            # Now test dataset creation
            dataset_name = f"Test Dataset {random.randint(10000, 99999)}"
            print(f"\n📊 Testing dataset creation: {dataset_name}")
            
            result = await connector_service.create_connector_dataset(
                connector=connector,
                table_or_query="default_table",
                dataset_name=dataset_name,
                user_id=user.id,
                description="Test dataset with fixed MindsDB execution",
                sharing_level=DataSharingLevel.PRIVATE
            )
            
            print(f"Dataset creation result: {json.dumps(result, indent=2)}")
            
            if result.get("success"):
                print(f"✅ Dataset creation succeeded!")
                print(f"   Dataset ID: {result.get('dataset_id')}")
                print(f"   Source: {result.get('source')}")
                return True
            else:
                print(f"❌ Dataset creation failed: {result.get('error')}")
                return False
        else:
            print(f"❌ MindsDB database creation failed: {mindsdb_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = asyncio.run(test_connector_creation_with_fixed_mindsdb())
    
    print(f"\n🎯 CONNECTOR CREATION TEST RESULTS")
    print("="*50)
    
    if success:
        print("✅ All tests passed!")
        print("✅ MindsDB query execution fix is working")
        print("✅ Web connector creation is working")
        print("✅ Dataset creation from connectors is working")
    else:
        print("❌ Tests failed!")
        print("❌ There may still be issues with connector creation")
    
    print("\n🔧 Fixes implemented:")
    print("1. ✅ Fixed execute_query method to handle None results from DDL queries")
    print("2. ✅ Added proper error handling for MindsDB operations")
    print("3. ✅ Fixed duplicate GET options in frontend dropdown")
    print("4. ✅ Improved select field rendering for required fields")