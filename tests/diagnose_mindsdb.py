#!/usr/bin/env python3
"""
Diagnose MindsDB model and engine issues.
Check what models and engines exist and their status.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.mindsdb import MindsDBService
from app.core.config import settings

def diagnose_mindsdb():
    """Diagnose MindsDB service and model status."""
    print("🔍 MindsDB Service Diagnosis")
    print("=" * 50)
    
    # Initialize MindsDB service
    mindsdb_service = MindsDBService()
    
    print(f"📍 MindsDB URL: {settings.MINDSDB_URL}")
    print(f"🔧 Engine Name: {settings.GEMINI_ENGINE_NAME}")
    print(f"🤖 Chat Model: {settings.GEMINI_CHAT_MODEL_NAME}")
    print(f"🎯 Default Model: {settings.DEFAULT_GEMINI_MODEL}")
    
    # Check connection
    print(f"\n🔗 Testing MindsDB Connection...")
    if mindsdb_service._ensure_connection():
        print("✅ MindsDB connection successful")
    else:
        print("❌ MindsDB connection failed")
        return
    
    # Check health
    print(f"\n🏥 Health Check...")
    health = mindsdb_service.health_check()
    print(f"   Status: {health.get('status')}")
    print(f"   Connection: {health.get('connection')}")
    
    # List all engines
    print(f"\n⚙️  Checking ML Engines...")
    try:
        engines_query = "SHOW ML_ENGINES"
        result = mindsdb_service.connection.query(engines_query)
        engines_df = result.fetch()
        
        if not engines_df.empty:
            print(f"   Found {len(engines_df)} engines:")
            for _, engine in engines_df.iterrows():
                print(f"      - {engine.get('NAME', 'Unknown')}: {engine.get('HANDLER', 'Unknown')}")
        else:
            print("   ❌ No ML engines found")
            
    except Exception as e:
        print(f"   ❌ Error checking engines: {e}")
    
    # Try to create Gemini engine
    print(f"\n🔧 Creating/Verifying Gemini Engine...")
    engine_result = mindsdb_service.create_gemini_engine()
    print(f"   Status: {engine_result.get('status')}")
    print(f"   Message: {engine_result.get('message')}")
    
    # List all models
    print(f"\n🤖 Checking Models...")
    try:
        models_query = "SHOW MODELS"
        result = mindsdb_service.connection.query(models_query)
        models_df = result.fetch()
        
        if not models_df.empty:
            print(f"   Found {len(models_df)} models:")
            for _, model in models_df.iterrows():
                model_name = model.get('NAME', 'Unknown')
                model_status = model.get('STATUS', 'Unknown')
                model_engine = model.get('ENGINE', 'Unknown')
                print(f"      - {model_name}: {model_status} (Engine: {model_engine})")
        else:
            print("   ❌ No models found")
            
    except Exception as e:
        print(f"   ❌ Error checking models: {e}")
    
    # Try to create the chat model
    print(f"\n🎯 Creating/Verifying Chat Model...")
    model_result = mindsdb_service.create_gemini_model(settings.GEMINI_CHAT_MODEL_NAME)
    print(f"   Status: {model_result.get('status')}")
    print(f"   Message: {model_result.get('message')}")
    
    # Test a simple chat
    print(f"\n💬 Testing Chat Functionality...")
    try:
        chat_result = mindsdb_service.ai_chat("Hello, can you respond?")
        if chat_result.get('error'):
            print(f"   ❌ Chat failed: {chat_result.get('error')}")
        else:
            print(f"   ✅ Chat successful!")
            print(f"   Response: {chat_result.get('answer', '')[:100]}...")
    except Exception as e:
        print(f"   ❌ Chat test failed: {e}")
    
    # Check database/project status
    print(f"\n📊 Database/Project Status...")
    try:
        # Check current database
        db_query = "SELECT DATABASE()"
        result = mindsdb_service.connection.query(db_query)
        db_df = result.fetch()
        if not db_df.empty:
            current_db = db_df.iloc[0, 0]
            print(f"   Current database: {current_db}")
        
        # List databases
        databases_query = "SHOW DATABASES"
        result = mindsdb_service.connection.query(databases_query)
        db_df = result.fetch()
        
        if not db_df.empty:
            print(f"   Available databases:")
            for _, db in db_df.iterrows():
                db_name = db.get('Database', 'Unknown')
                print(f"      - {db_name}")
        
    except Exception as e:
        print(f"   ❌ Error checking databases: {e}")
    
    print(f"\n" + "=" * 50)
    print("🔍 Diagnosis Complete")

def main():
    """Main function."""
    diagnose_mindsdb()

if __name__ == "__main__":
    main()