#!/usr/bin/env python3
"""
Direct test of MindsDB integration
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_mindsdb_direct():
    """Test MindsDB integration directly"""
    print("🧪 Testing MindsDB integration directly...")
    
    try:
        from app.services.mindsdb import mindsdb_service
        
        # Test connection
        print("1. Testing connection...")
        if mindsdb_service._ensure_connection():
            print("✅ MindsDB connection successful")
        else:
            print("❌ MindsDB connection failed")
            return False
        
        # Test health check
        print("2. Testing health check...")
        health = mindsdb_service.health_check()
        print(f"   Health status: {health.get('status')}")
        
        # Test engine creation
        print("3. Testing Gemini engine creation...")
        engine_result = mindsdb_service.create_gemini_engine()
        print(f"   Engine status: {engine_result.get('status')}")
        print(f"   Engine message: {engine_result.get('message')}")
        
        # Test model creation
        print("4. Testing Gemini model creation...")
        model_result = mindsdb_service.create_gemini_model("test_model")
        print(f"   Model status: {model_result.get('status')}")
        print(f"   Model message: {model_result.get('message')}")
        
        # Test direct query
        print("5. Testing direct MindsDB query...")
        try:
            query = "SELECT answer FROM mindsdb.test_model WHERE question = 'Hello, are you working?'"
            result = mindsdb_service.connection.query(query)
            
            if result and hasattr(result, 'fetch_all'):
                rows = result.fetch_all()
                print(f"   Query returned {len(rows)} rows")
                if rows:
                    print(f"   First row: {rows[0]}")
                else:
                    print("   No rows returned")
            else:
                print("   Query result is None or invalid")
                
        except Exception as e:
            print(f"   Query failed: {e}")
        
        # Test AI chat
        print("6. Testing AI chat...")
        chat_result = mindsdb_service.ai_chat("Hello, are you working correctly?")
        print(f"   Chat result: {chat_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ MindsDB direct test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 MINDSDB DIRECT TEST")
    print("=" * 60)
    
    success = test_mindsdb_direct()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"✅ MindsDB Direct Test: {'PASSED' if success else 'FAILED'}")
    print("=" * 60)
    
    sys.exit(0 if success else 1)