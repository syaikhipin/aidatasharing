#!/usr/bin/env python3
"""
Test existing MindsDB models
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_existing_models():
    """Test existing MindsDB models"""
    print("🧪 Testing existing MindsDB models...")
    
    try:
        import mindsdb_sdk
        
        # Connect to MindsDB
        print("1. Connecting to MindsDB...")
        connection = mindsdb_sdk.connect('http://127.0.0.1:47334')
        print("✅ Connected to MindsDB")
        
        # Use mindsdb project
        print("2. Using mindsdb project...")
        try:
            connection.query("USE mindsdb")
            print("✅ Using mindsdb project")
        except Exception as e:
            print(f"❌ Failed to use mindsdb project: {e}")
        
        # Test existing models
        existing_models = [
            "gemini_chat_assistant",
            "dataset_1_chat_model",
            "dataset_123_chat_model"
        ]
        
        for model_name in existing_models:
            print(f"3. Testing existing model: {model_name}")
            test_query = f"SELECT answer FROM {model_name} WHERE question = 'Hello, respond with SUCCESS'"
            
            try:
                result = connection.query(test_query)
                print(f"✅ Query executed for {model_name}, result type: {type(result)}")
                
                if result:
                    try:
                        if hasattr(result, 'fetch'):
                            data = result.fetch()
                            print(f"✅ Fetch returned: {data}")
                            if not data.empty:
                                print(f"✅ SUCCESS! Model {model_name} responded with data: {data}")
                                return True
                            else:
                                print(f"❌ Empty dataframe returned from {model_name}")
                        elif hasattr(result, 'fetch_all'):
                            rows = result.fetch_all()
                            print(f"✅ Got {len(rows) if rows else 0} rows from {model_name}")
                            if rows and len(rows) > 0:
                                print(f"✅ First row from {model_name}: {rows[0]}")
                                answer = rows[0].get('answer', '') if isinstance(rows[0], dict) else str(rows[0])
                                if answer:
                                    print(f"✅ SUCCESS! Model {model_name} responded: {answer}")
                                    return True
                                else:
                                    print(f"❌ No answer in response from {model_name}")
                            else:
                                print(f"❌ No rows returned from {model_name}")
                        else:
                            print(f"❌ Unknown result format from {model_name}: {dir(result)}")
                    except Exception as fetch_error:
                        print(f"❌ Error fetching result from {model_name}: {fetch_error}")
                else:
                    print(f"❌ No result returned from {model_name}")
                    
            except Exception as e:
                print(f"❌ Query failed for {model_name}: {e}")
                continue
        
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 EXISTING MODELS TEST")
    print("=" * 60)
    
    success = test_existing_models()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"✅ Existing Models Test: {'PASSED' if success else 'FAILED'}")
    print("=" * 60)
    
    sys.exit(0 if success else 1)