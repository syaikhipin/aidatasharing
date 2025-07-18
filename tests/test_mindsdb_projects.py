#!/usr/bin/env python3
"""
Test MindsDB projects and models
"""

import sys
import os
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_mindsdb_projects():
    """Test MindsDB projects and models"""
    print("🧪 Testing MindsDB projects...")
    
    try:
        import mindsdb_sdk
        
        # Connect to MindsDB
        print("1. Connecting to MindsDB...")
        connection = mindsdb_sdk.connect('http://127.0.0.1:47334')
        print("✅ Connected to MindsDB")
        
        # List projects
        print("2. Listing projects...")
        try:
            projects_result = connection.query("SHOW DATABASES")
            projects = projects_result.fetch()
            print(f"✅ Available projects/databases: {projects}")
        except Exception as e:
            print(f"❌ Failed to list projects: {e}")
        
        # List models in mindsdb project
        print("3. Listing models in mindsdb project...")
        try:
            models_result = connection.query("SHOW MODELS FROM mindsdb")
            models = models_result.fetch()
            print(f"✅ Available models in mindsdb: {models}")
        except Exception as e:
            print(f"❌ Failed to list models in mindsdb: {e}")
        
        # Try to use mindsdb project explicitly
        print("4. Using mindsdb project...")
        try:
            connection.query("USE mindsdb")
            print("✅ Using mindsdb project")
        except Exception as e:
            print(f"❌ Failed to use mindsdb project: {e}")
        
        # Create Gemini engine in mindsdb project
        print("5. Creating Gemini engine in mindsdb...")
        api_key = "AIzaSyB5-NF7TEYHkKdIMvZ45UNy1bDOCSCZH9Q"
        
        create_engine_sql = f"""
        CREATE ML_ENGINE IF NOT EXISTS project_google_gemini_engine
        FROM google_gemini
        USING
            api_key = '{api_key}';
        """
        
        try:
            connection.query(create_engine_sql)
            print("✅ Gemini engine created in mindsdb")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("✅ Gemini engine already exists in mindsdb")
            else:
                print(f"❌ Engine creation failed: {e}")
                return False
        
        # Create a simple model in mindsdb project
        print("6. Creating simple Gemini model in mindsdb...")
        create_model_sql = """
        CREATE MODEL project_gemini_test
        PREDICT answer
        USING
            engine = 'project_google_gemini_engine',
            model = 'gemini-2.0-flash';
        """
        
        try:
            connection.query(create_model_sql)
            print("✅ Simple model created in mindsdb")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("✅ Simple model already exists in mindsdb")
            else:
                print(f"❌ Model creation failed: {e}")
                return False
        
        # Wait for model to be ready
        print("7. Waiting for model to initialize...")
        time.sleep(10)
        
        # Test the model
        print("8. Testing the model...")
        test_query = "SELECT answer FROM project_gemini_test WHERE question = 'Hello, respond with SUCCESS'"
        
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
        
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 MINDSDB PROJECTS TEST")
    print("=" * 60)
    
    success = test_mindsdb_projects()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"✅ MindsDB Projects Test: {'PASSED' if success else 'FAILED'}")
    print("=" * 60)
    
    sys.exit(0 if success else 1)