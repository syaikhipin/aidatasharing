#!/usr/bin/env python3
"""
Test script for enhanced dataset chat functionality with web connector support.
Tests both regular uploaded datasets and web connector datasets.
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import get_db
from app.models.dataset import Dataset
from app.services.mindsdb import MindsDBService
from app.core.config import settings

async def test_web_connector_chat():
    """Test chat functionality with web connector datasets."""
    print("🧪 Testing Enhanced Dataset Chat Functionality")
    print("=" * 60)
    
    # Initialize services
    mindsdb_service = MindsDBService()
    
    # Get database session
    db = next(get_db())
    
    try:
        # Find datasets to test
        print("\n📊 Finding datasets to test...")
        
        # Look for web connector datasets (those with connector_id or source_url)
        web_connector_datasets = db.query(Dataset).filter(
            (Dataset.connector_id.isnot(None)) | (Dataset.source_url.isnot(None))
        ).limit(3).all()
        
        # Look for regular uploaded datasets
        uploaded_datasets = db.query(Dataset).filter(
            Dataset.connector_id.is_(None),
            Dataset.source_url.is_(None)
        ).limit(2).all()
        
        print(f"📡 Found {len(web_connector_datasets)} web connector datasets")
        print(f"📁 Found {len(uploaded_datasets)} uploaded datasets")
        
        if not web_connector_datasets and not uploaded_datasets:
            print("❌ No datasets found to test. Please create some datasets first.")
            return
        
        # Test web connector datasets
        if web_connector_datasets:
            print("\n🌐 Testing Web Connector Dataset Chat")
            print("-" * 40)
            
            for dataset in web_connector_datasets:
                print(f"\n🔍 Testing dataset: {dataset.name} (ID: {dataset.id})")
                print(f"   Source URL: {dataset.source_url}")
                print(f"   Connector ID: {dataset.connector_id}")
                
                # Test with a sample question
                test_message = "What does this dataset contain? Can you provide an overview of the data structure and any interesting patterns?"
                
                try:
                    result = mindsdb_service.chat_with_dataset(
                        dataset_id=str(dataset.id),
                        message=test_message,
                        user_id=1,  # Test user ID
                        session_id="test_session_web_connector"
                    )
                    
                    if result.get("error"):
                        print(f"   ❌ Error: {result['error']}")
                    else:
                        print(f"   ✅ Chat successful!")
                        print(f"   🤖 Model: {result.get('model', 'unknown')}")
                        print(f"   🔗 Source: {result.get('source', 'unknown')}")
                        print(f"   🌐 Web Connector: {result.get('is_web_connector', False)}")
                        print(f"   ⏱️  Response time: {result.get('response_time_seconds', 0):.2f}s")
                        
                        # Show first 200 characters of the answer
                        answer = result.get('answer', '')
                        preview = answer[:200] + "..." if len(answer) > 200 else answer
                        print(f"   💬 Answer preview: {preview}")
                        
                        # Check for web connector specific information
                        if result.get('web_connector_info'):
                            print(f"   🔗 Web connector info: {result['web_connector_info']}")
                
                except Exception as e:
                    print(f"   ❌ Exception during chat: {e}")
                
                print()
        
        # Test uploaded datasets
        if uploaded_datasets:
            print("\n📁 Testing Uploaded Dataset Chat")
            print("-" * 40)
            
            for dataset in uploaded_datasets:
                print(f"\n🔍 Testing dataset: {dataset.name} (ID: {dataset.id})")
                print(f"   Type: {dataset.type}")
                print(f"   Rows: {dataset.row_count}")
                print(f"   Columns: {dataset.column_count}")
                
                # Test with a sample question
                test_message = "What are the key characteristics of this dataset? Can you analyze the data structure and provide insights?"
                
                try:
                    result = mindsdb_service.chat_with_dataset(
                        dataset_id=str(dataset.id),
                        message=test_message,
                        user_id=1,  # Test user ID
                        session_id="test_session_uploaded"
                    )
                    
                    if result.get("error"):
                        print(f"   ❌ Error: {result['error']}")
                    else:
                        print(f"   ✅ Chat successful!")
                        print(f"   🤖 Model: {result.get('model', 'unknown')}")
                        print(f"   🔗 Source: {result.get('source', 'unknown')}")
                        print(f"   🌐 Web Connector: {result.get('is_web_connector', False)}")
                        print(f"   ⏱️  Response time: {result.get('response_time_seconds', 0):.2f}s")
                        
                        # Show first 200 characters of the answer
                        answer = result.get('answer', '')
                        preview = answer[:200] + "..." if len(answer) > 200 else answer
                        print(f"   💬 Answer preview: {preview}")
                
                except Exception as e:
                    print(f"   ❌ Exception during chat: {e}")
                
                print()
        
        # Test with different types of questions
        if web_connector_datasets:
            print("\n🎯 Testing Different Question Types on Web Connector Dataset")
            print("-" * 60)
            
            test_dataset = web_connector_datasets[0]
            test_questions = [
                "How fresh is this data? When was it last updated?",
                "What are the current trends in this real-time data?",
                "Are there any API limitations I should be aware of?",
                "How does the live nature of this data affect analysis?",
                "What visualizations would work best for this API data?"
            ]
            
            for i, question in enumerate(test_questions, 1):
                print(f"\n📝 Question {i}: {question}")
                
                try:
                    result = mindsdb_service.chat_with_dataset(
                        dataset_id=str(test_dataset.id),
                        message=question,
                        user_id=1,
                        session_id=f"test_questions_{i}"
                    )
                    
                    if result.get("error"):
                        print(f"   ❌ Error: {result['error']}")
                    else:
                        print(f"   ✅ Response received ({result.get('response_time_seconds', 0):.2f}s)")
                        
                        # Check if response mentions web connector concepts
                        answer = result.get('answer', '').lower()
                        web_concepts = ['api', 'real-time', 'live', 'fresh', 'endpoint', 'connector']
                        mentioned_concepts = [concept for concept in web_concepts if concept in answer]
                        
                        if mentioned_concepts:
                            print(f"   🌐 Web concepts mentioned: {', '.join(mentioned_concepts)}")
                        else:
                            print(f"   ⚠️  No web-specific concepts detected in response")
                
                except Exception as e:
                    print(f"   ❌ Exception: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Enhanced Dataset Chat Testing Complete!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def main():
    """Main test function."""
    print("🚀 Starting Enhanced Dataset Chat Test")
    print(f"📍 Backend directory: {backend_dir}")
    print(f"🔧 MindsDB URL: {settings.MINDSDB_URL}")
    
    # Run the async test
    asyncio.run(test_web_connector_chat())

if __name__ == "__main__":
    main()