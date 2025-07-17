#!/usr/bin/env python3
"""
Comprehensive migration script to fix all missing columns in the database
"""

import sqlite3
import logging
import os
import sys
from datetime import datetime

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.core.config import settings

logger = logging.getLogger(__name__)

def run_migration():
    """Run a comprehensive migration to fix all missing columns"""
    try:
        # Extract database path from DATABASE_URL
        db_path = settings.DATABASE_URL.replace('sqlite:///', '')
        
        logger.info(f"Starting comprehensive database migration on {db_path}...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Fix datasets table
        fix_datasets_table(cursor)
        
        # Fix dataset_downloads table
        fix_dataset_downloads_table(cursor)
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        logger.info("Comprehensive migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def fix_datasets_table(cursor):
    """Fix the datasets table by adding missing columns"""
    logger.info("Fixing datasets table...")
    
    # Check if the table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='datasets'
    """)
    
    if not cursor.fetchone():
        logger.info("datasets table doesn't exist, will be created by SQLAlchemy")
        return
    
    # Get current columns
    cursor.execute("PRAGMA table_info(datasets)")
    existing_columns = {row[1]: row[2] for row in cursor.fetchall()}
    
    logger.info(f"Current columns in datasets table: {list(existing_columns.keys())}")
    
    # Define the columns we need
    required_columns = {
        'file_path': 'VARCHAR',
        'preview_data': 'JSON',
        'schema_metadata': 'JSON',
        'quality_metrics': 'JSON',
        'column_statistics': 'JSON',
        'download_count': 'INTEGER',
        'last_downloaded_at': 'DATETIME'
    }
    
    # Add missing columns
    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            logger.info(f"Adding column to datasets table: {column_name}")
            
            # Set default values based on column type
            if column_name == 'download_count':
                cursor.execute(f"ALTER TABLE datasets ADD COLUMN {column_name} {column_type} DEFAULT 0")
            else:
                cursor.execute(f"ALTER TABLE datasets ADD COLUMN {column_name} {column_type}")
    
    logger.info("Datasets table fixed successfully!")

def fix_dataset_downloads_table(cursor):
    """Fix the dataset_downloads table by adding missing columns"""
    logger.info("Fixing dataset_downloads table...")
    
    # Check if the table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='dataset_downloads'
    """)
    
    if not cursor.fetchone():
        logger.info("dataset_downloads table doesn't exist, will be created by SQLAlchemy")
        return
    
    # Get current columns
    cursor.execute("PRAGMA table_info(dataset_downloads)")
    existing_columns = {row[1]: row[2] for row in cursor.fetchall()}
    
    logger.info(f"Current columns in dataset_downloads table: {list(existing_columns.keys())}")
    
    # Define the columns we need
    required_columns = {
        'download_token': 'VARCHAR',
        'file_format': 'VARCHAR',
        'compression': 'VARCHAR',
        'original_filename': 'VARCHAR',
        'file_size_bytes': 'INTEGER',
        'download_status': 'VARCHAR',
        'progress_percentage': 'INTEGER',
        'error_message': 'TEXT',
        'expires_at': 'DATETIME',
        'download_duration_seconds': 'INTEGER',
        'transfer_rate_mbps': 'VARCHAR',
        'updated_at': 'DATETIME'
    }
    
    # Add missing columns
    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            logger.info(f"Adding column to dataset_downloads table: {column_name}")
            
            # Set default values based on column type
            if column_name == 'download_token':
                # Generate unique tokens for existing records
                cursor.execute("SELECT id FROM dataset_downloads")
                existing_ids = [row[0] for row in cursor.fetchall()]
                
                cursor.execute(f"ALTER TABLE dataset_downloads ADD COLUMN {column_name} {column_type}")
                
                # Update existing records with unique tokens
                import uuid
                for record_id in existing_ids:
                    token = str(uuid.uuid4())
                    cursor.execute(
                        "UPDATE dataset_downloads SET download_token = ? WHERE id = ?",
                        (token, record_id)
                    )
            elif column_name == 'file_format':
                cursor.execute(f"ALTER TABLE dataset_downloads ADD COLUMN {column_name} {column_type} DEFAULT 'original'")
            elif column_name == 'download_status':
                cursor.execute(f"ALTER TABLE dataset_downloads ADD COLUMN {column_name} {column_type} DEFAULT 'completed'")
            elif column_name == 'progress_percentage':
                cursor.execute(f"ALTER TABLE dataset_downloads ADD COLUMN {column_name} {column_type} DEFAULT 100")
            elif column_name == 'updated_at':
                cursor.execute(f"ALTER TABLE dataset_downloads ADD COLUMN {column_name} {column_type} DEFAULT CURRENT_TIMESTAMP")
            else:
                cursor.execute(f"ALTER TABLE dataset_downloads ADD COLUMN {column_name} {column_type}")
    
    # Create index on download_token for performance
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_dataset_downloads_token ON dataset_downloads(download_token)")
    except sqlite3.OperationalError as e:
        if "already exists" not in str(e):
            raise
    
    logger.info("Dataset_downloads table fixed successfully!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_migration()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        exit(1)