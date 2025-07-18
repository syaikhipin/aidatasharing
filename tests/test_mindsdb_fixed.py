#!/usr/bin/env python3
"""
Fixed test of MindsDB Gemini integration
"""

import sys
import os
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_mindsdb_fixed():
    """Fixed test of MindsDB Gemini integration"""
    print("🧪 Fixed MindsDB Gemini test...")
    
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
        CREATE ML_ENGINE IF NOT EXISTS fixed_google_gemini_engine
        FROM google_gemini
        USING
            api_key = '{api_key}';
        """
        
        try:
            connection.query(create_engine_sql)
            print("✅ Gemini engine created")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("✅ Gemini engine already exists")
            else:
                print(f"❌ Engine creation failed: {e}")
                return False
        
        # Create a simple model without mindsdb prefix
        print("3. Creating simple Gemini model...")
        create_model_sql = """
        CREATE MODEL fixed_gemini_test
        PREDICT answer
        USING
            engine = 'fixed_google_gemini_engine',
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
        time.sleep(10)
        
        # Test the model with corrected queries
        print("5. Testing the model...")
        test_queries = [
            "SELECT answer FROM fixed_gemini_test WHERE question = 'Hello'",
            "SELECT answer FROM fixed_gemini_test WHERE question = 'What is 2+2?'",
            "SELECT answer FROM fixed_gemini_test WHERE question = 'Say SUCCESS if you are working'"
        ]
        
        for i, test_query in enumerate(test_queries, 1):
            print(f"5.{i} Testing query: {test_query}")
            try:
                result = connection.query(test_query)
                print(f"✅ Query executed, result type: {type(result)}")
                
                if result:
                    try:
                        if hasattr(result, 'fetch'):
                            data = result.fetch()
                            print(f"✅ Fetch returned: {data}")
                            if not data.empty:
                                print(f"✅ SUCCESS! Model responded with data: {data}")
                                return True
                            else:
                                print("❌ Empty dataframe returned")
                        elif hasattr(result, 'fetch_all'):
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
                        else:
                            print(f"❌ Unknown result format: {dir(result)}")
                    except Exception as fetch_error:
                        print(f"❌ Error fetching result: {fetch_error}")
                else:
                    print("❌ No result returned")
                    
            except Exception as e:
                print(f"❌ Query failed: {e}")
                continue
        
        print("❌ All queries failed to return valid responses")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 FIXED MINDSDB GEMINI TEST")
    print("=" * 60)
    
    success = test_mindsdb_fixed()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"✅ Fixed MindsDB Test: {'PASSED' if success else 'FAILED'}")
    print("=" * 60)
    
    sys.exit(0 if success else 1)