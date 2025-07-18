#!/usr/bin/env python3
"""
Simple test of MindsDB Gemini integration
"""

import sys
import os
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_mindsdb_simple():
    """Test MindsDB Gemini integration with simple approach"""
    print("🧪 Testing MindsDB Gemini integration...")
    
    try:
        import mindsdb_sdk
        
        # Connect to MindsDB
        print("1. Connecting to MindsDB...")
        connection = mindsdb_sdk.connect('http://127.0.0.1:47334')
        print("✅ Connected to MindsDB")
        
        # Create Gemini engine
        print("2. Creating Gemini engine...")
        api_key = "AIzaSyB5-NF7TEYHkKdIMvZ45UNy1bDOCSCZH9Q"
        
        create_engine_sql = f"""
        CREATE ML_ENGINE IF NOT EXISTS google_gemini_engine
        FROM google_gemini
        USING
            api_key = '{api_key}';
        """
        
        try:
            connection.query(create_engine_sql)
            print("✅ Gemini engine created/verified")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("✅ Gemini engine already exists")
            else:
                print(f"❌ Engine creation failed: {e}")
                return False
        
        # Create a simple model
        print("3. Creating simple Gemini model...")
        create_model_sql = """
        CREATE MODEL IF NOT EXISTS mindsdb.simple_gemini_test
        PREDICT answer
        USING
            engine = 'google_gemini_engine',
            model = 'gemini-2.0-flash';
        """
        
        try:
            connection.query(create_model_sql)
            print("✅ Simple model created")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("✅ Simple model already exists")
            else:
                print(f"❌ Model creation failed: {e}")
                return False
        
        # Wait for model to be ready
        print("4. Waiting for model to initialize...")
        time.sleep(5)
        
        # Test the model
        print("5. Testing the model...")
        test_query = """
        SELECT answer 
        FROM mindsdb.simple_gemini_test 
        WHERE question = 'Hello, can you respond with just the word SUCCESS?'
        """
        
        try:
            result = connection.query(test_query)
            print(f"✅ Query executed, result type: {type(result)}")
            
            if result:
                if hasattr(result, 'fetch_all'):
                    rows = result.fetch_all()
                    print(f"✅ Got {len(rows) if rows else 0} rows")
                    if rows and len(rows) > 0:
                        print(f"✅ First row: {rows[0]}")
                        answer = rows[0].get('answer', '') if isinstance(rows[0], dict) else str(rows[0])
                        if answer:
                            print(f"✅ SUCCESS! Model responded: {answer}")
                            return True
                        else:
                            print("❌ No answer in response")
                    else:
                        print("❌ No rows returned")
                elif hasattr(result, 'fetch'):
                    data = result.fetch()
                    print(f"✅ Fetch returned: {data}")
                    if not data.empty:
                        print(f"✅ SUCCESS! Model responded: {data}")
                        return True
                    else:
                        print("❌ Empty dataframe returned")
                else:
                    print(f"❌ Unknown result format: {dir(result)}")
            else:
                print("❌ No result returned")
                
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return False
        
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 MINDSDB SIMPLE GEMINI TEST")
    print("=" * 60)
    
    success = test_mindsdb_simple()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"✅ MindsDB Gemini Test: {'PASSED' if success else 'FAILED'}")
    print("=" * 60)
    
    sys.exit(0 if success else 1)