#!/usr/bin/env python3
"""
Debug MindsDB integration
"""

import sys
import os
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_mindsdb_debug():
    """Debug MindsDB integration"""
    print("🧪 Debugging MindsDB integration...")
    
    try:
        import mindsdb_sdk
        
        # Connect to MindsDB
        print("1. Connecting to MindsDB...")
        connection = mindsdb_sdk.connect('http://127.0.0.1:47334')
        print("✅ Connected to MindsDB")
        
        # List available engines
        print("2. Listing available engines...")
        try:
            engines_result = connection.query("SHOW ML_ENGINES")
            engines = engines_result.fetch()
            print(f"✅ Available engines: {engines}")
        except Exception as e:
            print(f"❌ Failed to list engines: {e}")
        
        # List available models
        print("3. Listing available models...")
        try:
            models_result = connection.query("SHOW MODELS")
            models = models_result.fetch()
            print(f"✅ Available models: {models}")
        except Exception as e:
            print(f"❌ Failed to list models: {e}")
        
        # Check if google_gemini handler is available
        print("4. Checking available handlers...")
        try:
            handlers_result = connection.query("SHOW HANDLERS")
            handlers = handlers_result.fetch()
            print(f"✅ Available handlers: {handlers}")
            
            # Check if google_gemini is in the handlers
            if hasattr(handlers, 'to_dict'):
                handlers_dict = handlers.to_dict()
                print(f"✅ Handlers dict: {handlers_dict}")
            
        except Exception as e:
            print(f"❌ Failed to list handlers: {e}")
        
        # Try to create engine with different approach
        print("5. Creating Gemini engine with debug...")
        api_key = "AIzaSyB5-NF7TEYHkKdIMvZ45UNy1bDOCSCZH9Q"
        
        # First check if the handler exists
        try:
            handler_check = connection.query("SELECT * FROM information_schema.handlers WHERE name = 'google_gemini'")
            handler_info = handler_check.fetch()
            print(f"✅ Google Gemini handler info: {handler_info}")
        except Exception as e:
            print(f"❌ Handler check failed: {e}")
        
        # Try creating engine
        create_engine_sql = f"""
        CREATE ML_ENGINE IF NOT EXISTS test_gemini_engine
        FROM google_gemini
        USING
            api_key = '{api_key}';
        """
        
        try:
            connection.query(create_engine_sql)
            print("✅ Test Gemini engine created")
        except Exception as e:
            print(f"❌ Engine creation failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Debug test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 MINDSDB DEBUG TEST")
    print("=" * 60)
    
    success = test_mindsdb_debug()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"✅ MindsDB Debug Test: {'PASSED' if success else 'FAILED'}")
    print("=" * 60)
    
    sys.exit(0 if success else 1)