#!/usr/bin/env python3
"""
Create test datasets for enhanced chat functionality testing.
Creates both a web connector dataset and an uploaded dataset.
"""

import sys
import os
import asyncio
import json
from pathlib import Path
from datetime import datetime

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import get_db
from app.models.dataset import Dataset, DatasetType, DatasetStatus, DataSharingLevel
from app.models.user import User
from app.services.mindsdb import MindsDBService

async def create_test_datasets():
    """Create test datasets for chat functionality testing."""
    print("🏗️  Creating Test Datasets for Enhanced Chat")
    print("=" * 50)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Find or create a test user
        test_user = db.query(User).filter(User.email == "demo1@demo.com").first()
        if not test_user:
            print("❌ No test user found. Please create a test user first.")
            return
        
        print(f"👤 Using test user: {test_user.email} (ID: {test_user.id})")
        
        # Initialize MindsDB service
        mindsdb_service = MindsDBService()
        
        # 1. Create a web connector dataset using JSONPlaceholder API
        print("\n🌐 Creating Web Connector Dataset...")
        
        # Create web connector
        web_connector_result = mindsdb_service.create_web_connector(
            connector_name="test_jsonplaceholder_posts",
            base_url="https://jsonplaceholder.typicode.com",
            endpoint="/posts",
            method="GET"
        )
        
        if web_connector_result.get("success"):
            print(f"✅ Web connector created: {web_connector_result['connector_name']}")
            
            # Create dataset view
            dataset_view_result = mindsdb_service.create_dataset_from_web_connector(
                connector_name=web_connector_result["connector_name"],
                dataset_name="JSONPlaceholder Posts",
                table_name="data"
            )
            
            if dataset_view_result.get("success"):
                print(f"✅ Dataset view created: {dataset_view_result['view_name']}")
                
                # Create dataset record in database
                web_dataset = Dataset(
                    name="JSONPlaceholder Posts",
                    description="Sample blog posts from JSONPlaceholder API for testing web connector chat functionality",
                    type=DatasetType.JSON,
                    status=DatasetStatus.ACTIVE,
                    owner_id=test_user.id,
                    organization_id=test_user.organization_id,
                    sharing_level=DataSharingLevel.ORGANIZATION,
                    source_url=web_connector_result["url"],
                    connector_id=web_connector_result["connector_name"],
                    row_count=dataset_view_result.get("estimated_rows", 100),
                    column_count=len(dataset_view_result.get("columns", [])),
                    allow_download=True,
                    allow_api_access=True,
                    allow_ai_chat=True,
                    schema_info={
                        "columns": dataset_view_result.get("columns", []),
                        "sample_data": dataset_view_result.get("sample_data", [])
                    },
                    schema_metadata={
                        "data_source": "web_connector",
                        "api_endpoint": web_connector_result["url"],
                        "connector_name": web_connector_result["connector_name"],
                        "data_freshness": "real-time",
                        "created_at": datetime.utcnow().isoformat()
                    },
                    quality_metrics={
                        "overall_score": 0.9,
                        "completeness": 1.0,
                        "consistency": 0.9,
                        "accuracy": 0.9,
                        "issues": [],
                        "last_analyzed": datetime.utcnow().isoformat()
                    },
                    preview_data={
                        "headers": dataset_view_result.get("columns", []),
                        "sample_rows": dataset_view_result.get("sample_data", [])[:5],
                        "total_rows": dataset_view_result.get("estimated_rows", 100),
                        "is_sample": True,
                        "preview_generated_at": datetime.utcnow().isoformat()
                    }
                )
                
                db.add(web_dataset)
                db.commit()
                db.refresh(web_dataset)
                
                print(f"✅ Web connector dataset created in database: ID {web_dataset.id}")
            else:
                print(f"❌ Failed to create dataset view: {dataset_view_result.get('error')}")
        else:
            print(f"❌ Failed to create web connector: {web_connector_result.get('error')}")
        
        # 2. Create a mock uploaded dataset for comparison
        print("\n📁 Creating Mock Uploaded Dataset...")
        
        uploaded_dataset = Dataset(
            name="Sample Sales Data",
            description="Mock sales data for testing uploaded dataset chat functionality",
            type=DatasetType.CSV,
            status=DatasetStatus.ACTIVE,
            owner_id=test_user.id,
            organization_id=test_user.organization_id,
            sharing_level=DataSharingLevel.ORGANIZATION,
            row_count=1000,
            column_count=8,
            size_bytes=50000,
            allow_download=True,
            allow_api_access=True,
            allow_ai_chat=True,
            schema_info={
                "columns": ["id", "date", "product", "category", "quantity", "price", "customer_id", "region"],
                "sample_data": [
                    {"id": 1, "date": "2024-01-15", "product": "Widget A", "category": "Electronics", "quantity": 5, "price": 29.99, "customer_id": 101, "region": "North"},
                    {"id": 2, "date": "2024-01-16", "product": "Gadget B", "category": "Electronics", "quantity": 2, "price": 149.99, "customer_id": 102, "region": "South"}
                ]
            },
            schema_metadata={
                "data_source": "uploaded_file",
                "file_type": "csv",
                "encoding": "utf-8",
                "columns": ["id", "date", "product", "category", "quantity", "price", "customer_id", "region"],
                "data_types": {
                    "id": "integer",
                    "date": "date",
                    "product": "string",
                    "category": "string",
                    "quantity": "integer",
                    "price": "float",
                    "customer_id": "integer",
                    "region": "string"
                },
                "created_at": datetime.utcnow().isoformat()
            },
            quality_metrics={
                "overall_score": 0.95,
                "completeness": 1.0,
                "consistency": 0.95,
                "accuracy": 0.95,
                "issues": [],
                "last_analyzed": datetime.utcnow().isoformat()
            },
            preview_data={
                "headers": ["id", "date", "product", "category", "quantity", "price", "customer_id", "region"],
                "sample_rows": [
                    [1, "2024-01-15", "Widget A", "Electronics", 5, 29.99, 101, "North"],
                    [2, "2024-01-16", "Gadget B", "Electronics", 2, 149.99, 102, "South"],
                    [3, "2024-01-17", "Tool C", "Hardware", 1, 79.99, 103, "East"]
                ],
                "total_rows": 1000,
                "is_sample": True,
                "preview_generated_at": datetime.utcnow().isoformat()
            }
        )
        
        db.add(uploaded_dataset)
        db.commit()
        db.refresh(uploaded_dataset)
        
        print(f"✅ Mock uploaded dataset created in database: ID {uploaded_dataset.id}")
        
        # List all datasets
        print("\n📊 Current Datasets in Database:")
        all_datasets = db.query(Dataset).all()
        for dataset in all_datasets:
            is_web_connector = bool(dataset.connector_id or dataset.source_url)
            print(f"  📋 ID: {dataset.id}, Name: {dataset.name}")
            print(f"      Type: {dataset.type}, Web Connector: {is_web_connector}")
            if is_web_connector:
                print(f"      Source URL: {dataset.source_url}")
                print(f"      Connector ID: {dataset.connector_id}")
            print()
        
        print("✅ Test datasets created successfully!")
        print("\n🧪 You can now run the enhanced chat test:")
        print("   python tests/test_enhanced_dataset_chat.py")
        
    except Exception as e:
        print(f"❌ Failed to create test datasets: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def main():
    """Main function."""
    print("🚀 Starting Test Dataset Creation")
    
    # Run the async function
    asyncio.run(create_test_datasets())

if __name__ == "__main__":
    main()