#!/usr/bin/env python3
"""
Migration script to ensure dataset_downloads table exists
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.database import Base
from app.models.dataset import DatasetDownload  # This will ensure the table is registered

def create_downloads_table():
    """Create the dataset_downloads table if it doesn't exist"""
    try:
        # Get database URL
        database_url = getattr(settings, 'DATABASE_URL', 'sqlite:///./storage/aishare_platform.db')
        
        # Handle SQLite URL format
        if database_url.startswith('sqlite:///'):
            db_path = database_url.replace('sqlite:///', '')
            if not os.path.isabs(db_path):
                db_path = os.path.join(os.path.dirname(__file__), db_path)
            database_url = f'sqlite:///{db_path}'
        
        print(f"Using database: {database_url}")
        
        # Create engine
        engine = create_engine(database_url, echo=True)
        
        # Check if table exists
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='dataset_downloads';
            """))
            table_exists = result.fetchone() is not None
            
        if table_exists:
            print("✅ dataset_downloads table already exists")
        else:
            print("❌ dataset_downloads table does not exist. Creating...")
            # Create all tables (this will only create missing ones)
            Base.metadata.create_all(bind=engine)
            print("✅ dataset_downloads table created successfully")
        
        # Verify table structure
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(dataset_downloads);"))
            columns = result.fetchall()
            print(f"✅ Table has {len(columns)} columns:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Migrating dataset_downloads table...")
    success = create_downloads_table()
    if success:
        print("✅ Migration completed successfully")
    else:
        print("❌ Migration failed")
        sys.exit(1)