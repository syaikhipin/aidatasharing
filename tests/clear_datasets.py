#!/usr/bin/env python3
"""
Clear all datasets, connectors, uploaded files, and sharing links
while preserving users and organizations
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(backend_dir))

# Load environment variables
from dotenv import load_dotenv
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment variables from {env_path}")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

def clear_all_data():
    """Clear all datasets, connectors, files, and sharing data"""
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("🧹 Starting data cleanup...")
        
        # List of tables to clear (in order to handle foreign key constraints)
        tables_to_clear = [
            # Chat and interaction related (clear first - they reference others)
            'chat_interactions',
            'chat_messages', 
            'dataset_chat_sessions',
            
            # Sharing and access related (clear second)
            'access_requests',  # Must be before datasets
            'dataset_share_accesses',
            'share_access_sessions',
            'shared_proxy_links',
            
            # Logs and analytics (clear third - they reference main tables)
            'file_processing_logs',  # Must be before file_uploads
            'dataset_access_logs',
            'proxy_access_logs',
            'datashare_stats',
            'usage_stats',
            'usage_metrics',
            'system_metrics',
            'model_performance_logs',
            'api_usage',
            'activity_logs',
            'audit_logs',
            
            # Dataset and file related (clear fourth)
            'dataset_access',
            'dataset_downloads', 
            'dataset_files',
            'dataset_models',
            'file_uploads',  # After file_processing_logs
            'datasets',
            
            # Connector and proxy related (clear last)
            'database_connectors',
            'proxy_connectors',
            'proxy_credential_vault',
            
            # MindsDB related
            'mindsdb_configurations',
            'mindsdb_handlers'
        ]
        
        # Count records before deletion
        total_deleted = 0
        
        for table in tables_to_clear:
            try:
                # Check if table exists and count records
                count_result = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                if count_result > 0:
                    print(f"📋 {table}: {count_result} records")
                    
                    # Delete all records from table
                    delete_result = session.execute(text(f"DELETE FROM {table}"))
                    deleted_count = delete_result.rowcount
                    total_deleted += deleted_count
                    print(f"  ✅ Deleted {deleted_count} records from {table}")
                else:
                    print(f"  ⚪ {table}: already empty")
                    
            except Exception as e:
                print(f"  ⚠️ {table}: {str(e)} (table might not exist)")
                continue
        
        # Commit all deletions
        session.commit()
        print(f"✅ Database cleanup completed - {total_deleted} total records deleted")
        
        # Clear uploaded files from storage
        print("\n🗂️ Clearing uploaded files...")
        clear_uploaded_files()
        
        # Verify users are still present
        print("\n👥 Verifying users are preserved...")
        verify_users(session)
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error during cleanup: {str(e)}")
        raise
    finally:
        session.close()

def clear_uploaded_files():
    """Clear uploaded files from storage directories"""
    
    storage_paths = [
        "../storage/uploads",
        "../storage/datasets", 
        "../storage/documents",
        "../storage/images",
        "../storage/temp"
    ]
    
    files_deleted = 0
    
    for storage_path in storage_paths:
        path = Path(storage_path)
        if path.exists():
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        files_deleted += 1
                    except Exception as e:
                        print(f"  ⚠️ Could not delete {file_path}: {e}")
            print(f"  ✅ Cleared {storage_path}")
        else:
            print(f"  ⚪ {storage_path}: directory doesn't exist")
    
    print(f"✅ Deleted {files_deleted} uploaded files")

def verify_users(session):
    """Verify that users are still present"""
    
    try:
        users = session.execute(text("SELECT email, is_superuser FROM users ORDER BY email")).fetchall()
        
        print(f"👥 Found {len(users)} users:")
        for user in users:
            role = "SuperAdmin" if user.is_superuser else "User"
            print(f"  ✅ {user.email} ({role})")
            
        orgs = session.execute(text("SELECT name FROM organizations ORDER BY name")).fetchall()
        print(f"🏢 Found {len(orgs)} organizations:")
        for org in orgs:
            print(f"  ✅ {org.name}")
            
    except Exception as e:
        print(f"⚠️ Could not verify users: {e}")

if __name__ == "__main__":
    print("🚀 AI Share Platform - Data Cleanup Script")
    print("=" * 50)
    print("This script will clear:")
    print("  ✅ All datasets")
    print("  ✅ All data connectors") 
    print("  ✅ All uploaded files")
    print("  ✅ All sharing links")
    print("  ✅ All chat sessions")
    print("  ✅ All models and analytics")
    print("")
    print("This script will preserve:")
    print("  👥 All users (admin, alice, bob, etc.)")
    print("  🏢 All organizations")
    print("=" * 50)
    
    response = input("Are you sure you want to proceed? (yes/no): ").lower().strip()
    if response in ['yes', 'y']:
        clear_all_data()
        print("\n🎉 Data cleanup completed successfully!")
    else:
        print("❌ Operation cancelled")