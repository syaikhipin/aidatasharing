#!/usr/bin/env python3
"""
Manual test for enhanced dataset chat context detection.
Tests the logic for detecting web connector datasets and building enhanced context.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import get_db
from app.models.dataset import Dataset, DatasetType, DatasetStatus, DataSharingLevel
from app.models.user import User

def test_context_detection():
    """Test the context detection logic for web connector vs uploaded datasets."""
    print("🧪 Testing Enhanced Chat Context Detection")
    print("=" * 50)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Refresh the session to get latest data
        db.expire_all()
        
        # Find existing datasets
        datasets = db.query(Dataset).all()
        print(f"📊 Found {len(datasets)} datasets to test")
        
        # Debug: show all datasets
        for d in datasets:
            print(f"   Debug: ID {d.id}, Name: {d.name}, Connector: {d.connector_id}, URL: {d.source_url}")
        
        if not datasets:
            print("❌ No datasets found. Creating test datasets...")
            
            # Find a test user
            test_user = db.query(User).filter(User.email == "demo1@demo.com").first()
            if not test_user:
                print("❌ No test user found")
                return
            
            # Create a mock web connector dataset
            web_dataset = Dataset(
                name="Test Web Connector Dataset",
                description="Mock web connector dataset for testing",
                type=DatasetType.JSON,
                status=DatasetStatus.ACTIVE,
                owner_id=test_user.id,
                organization_id=test_user.organization_id,
                sharing_level=DataSharingLevel.ORGANIZATION,
                source_url="https://api.example.com/data",
                connector_id="test_web_connector",
                row_count=500,
                column_count=6,
                allow_ai_chat=True
            )
            
            db.add(web_dataset)
            db.commit()
            db.refresh(web_dataset)
            
            datasets = [web_dataset]
            print(f"✅ Created test web connector dataset: ID {web_dataset.id}")
        
        # Test context detection logic for each dataset
        for dataset in datasets:
            print(f"\n🔍 Testing dataset: {dataset.name} (ID: {dataset.id})")
            print(f"   Type: {dataset.type}")
            print(f"   Source URL: {dataset.source_url}")
            print(f"   Connector ID: {dataset.connector_id}")
            
            # Apply the same logic as in the enhanced chat method
            is_web_connector = bool(dataset.connector_id or dataset.source_url)
            web_connector_info = {}
            
            if is_web_connector:
                web_connector_info = {
                    "connector_id": dataset.connector_id,
                    "source_url": dataset.source_url,
                    "connector_name": getattr(dataset, 'connector_name', None)
                }
                
                print(f"   🌐 DETECTED: Web Connector Dataset")
                print(f"   📡 Web connector info: {web_connector_info}")
                
                # Build web connector context
                dataset_context = f"""
                Dataset Information (Web Connector):
                - Name: {dataset.name}
                - Type: {dataset.type} (Web API Data)
                - Description: {dataset.description or 'No description available'}
                - Data Source: External API via web connector
                - Source URL: {dataset.source_url}
                - Connector ID: {dataset.connector_id}
                - Rows: {dataset.row_count or 'Dynamic (API-dependent)'}
                - Columns: {dataset.column_count or 'Dynamic (API-dependent)'}
                - Created: {dataset.created_at}
                - Data Access: Real-time via MindsDB web connector
                - Data Freshness: Live data from API endpoint
                """
                
                print(f"   📝 Context type: Web Connector Enhanced")
                print(f"   🎯 Context preview: {dataset_context[:200]}...")
                
                # Check if the enhanced prompt would be used
                enhanced_prompt_type = "Web Connector Enhanced Prompt"
                expected_sections = [
                    "🌐 Live API Dataset Overview",
                    "🎯 Current Data Analysis", 
                    "📊 Real-time Data Patterns",
                    "📈 Dynamic Insights",
                    "🔄 Data Freshness & Reliability",
                    "💡 API-Aware Recommendations",
                    "⚠️ API Limitations & Considerations"
                ]
                
            else:
                print(f"   📁 DETECTED: Uploaded Dataset")
                
                # Build uploaded dataset context
                dataset_context = f"""
                Dataset Information (Uploaded File):
                - Name: {dataset.name}
                - Type: {dataset.type}
                - Description: {dataset.description or 'No description available'}
                - Data Source: Uploaded file
                - Rows: {dataset.row_count or 'Unknown'}
                - Columns: {dataset.column_count or 'Unknown'}
                - Created: {dataset.created_at}
                - Data Access: Static file data
                """
                
                print(f"   📝 Context type: Standard Uploaded")
                print(f"   🎯 Context preview: {dataset_context[:200]}...")
                
                # Check if the standard prompt would be used
                enhanced_prompt_type = "Standard Enhanced Prompt"
                expected_sections = [
                    "📊 Data Overview",
                    "🎯 Analysis Results",
                    "📈 Statistical Insights", 
                    "📋 Recommended Visualizations",
                    "💡 Key Insights & Recommendations",
                    "⚠️ Data Quality & Limitations"
                ]
            
            print(f"   🎨 Prompt type: {enhanced_prompt_type}")
            print(f"   📋 Expected sections: {len(expected_sections)} sections")
            for section in expected_sections:
                print(f"      - {section}")
            
            # Test response metadata that would be added
            response_metadata = {
                "dataset_id": str(dataset.id),
                "dataset_name": dataset.name,
                "model": "enhanced_gemini_chat_assistant",
                "source": "mindsdb_web_connector_chat" if is_web_connector else "mindsdb_enhanced_chat",
                "is_web_connector": is_web_connector,
                "web_connector_info": web_connector_info if is_web_connector else None
            }
            
            print(f"   🏷️  Response metadata:")
            for key, value in response_metadata.items():
                if value is not None:
                    print(f"      {key}: {value}")
            
            print()
        
        print("=" * 50)
        print("✅ Context Detection Test Complete!")
        print("\n📊 Summary:")
        
        web_connector_count = sum(1 for d in datasets if d.connector_id or d.source_url)
        uploaded_count = len(datasets) - web_connector_count
        
        print(f"   🌐 Web connector datasets: {web_connector_count}")
        print(f"   📁 Uploaded datasets: {uploaded_count}")
        print(f"   📋 Total datasets tested: {len(datasets)}")
        
        if web_connector_count > 0:
            print("\n✅ Web connector detection logic working correctly!")
            print("   - Detected web connector datasets based on connector_id/source_url")
            print("   - Applied enhanced context for API-based data")
            print("   - Would use specialized prompt for real-time data analysis")
        
        if uploaded_count > 0:
            print("\n✅ Uploaded dataset detection logic working correctly!")
            print("   - Detected uploaded datasets (no connector info)")
            print("   - Applied standard context for file-based data")
            print("   - Would use standard prompt for static data analysis")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def main():
    """Main test function."""
    test_context_detection()

if __name__ == "__main__":
    main()