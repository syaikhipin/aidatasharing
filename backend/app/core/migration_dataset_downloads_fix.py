#!/usr/bin/env python3
"""
Migration to fix dataset_downloads table schema
Adds missing columns and updates existing ones to match the new model
"""

import sqlite3
import logging
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)

def run_migration():
    """Run the dataset_downloads table migration"""
    try:
        # Extract database path from DATABASE_URL
        db_path = settings.DATABASE_URL.replace('sqlite:///', '')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("Starting dataset_downloads table migration...")
        
        # Check if the table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='dataset_downloads'
        """)
        
        if not cursor.fetchone():
            logger.info("dataset_downloads table doesn't exist, will be created by SQLAlchemy")
            conn.close()
            return True
        
        # Get current columns
        cursor.execute("PRAGMA table_info(dataset_downloads)")
        existing_columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        logger.info(f"Current columns: {list(existing_columns.keys())}")
        
        # Define the columns we need (based on the new model)
        required_columns = {
            'download_token': 'VARCHAR',
            'compression': 'VARCHAR',
            'original_filename': 'VARCHAR',
            'download_status': 'VARCHAR',
            'progress_percentage': 'INTEGER',
            'expires_at': 'DATETIME',
            'download_duration_seconds': 'INTEGER',
            'transfer_rate_mbps': 'VARCHAR',
            'updated_at': 'DATETIME'
        }
        
        # Add missing columns
        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                logger.info(f"Adding column: {column_name}")
                
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
                        
                elif column_name == 'download_status':
                    cursor.execute(f"ALTER TABLE dataset_downloads ADD COLUMN {column_name} {column_type} DEFAULT 'completed'")
                elif column_name == 'progress_percentage':
                    cursor.execute(f"ALTER TABLE dataset_downloads ADD COLUMN {column_name} {column_type} DEFAULT 100")
                elif column_name == 'download_duration_seconds':
                    cursor.execute(f"ALTER TABLE dataset_downloads ADD COLUMN {column_name} {column_type}")
                    # Update from existing duration_seconds if it exists
                    if 'duration_seconds' in existing_columns:
                        cursor.execute("UPDATE dataset_downloads SET download_duration_seconds = CAST(duration_seconds AS INTEGER)")
                elif column_name == 'updated_at':
                    cursor.execute(f"ALTER TABLE dataset_downloads ADD COLUMN {column_name} {column_type} DEFAULT CURRENT_TIMESTAMP")
                else:
                    cursor.execute(f"ALTER TABLE dataset_downloads ADD COLUMN {column_name} {column_type}")
        
        # Remove columns that are no longer needed
        columns_to_remove = ['download_id', 'download_method', 'duration_seconds', 'success', 'bytes_transferred']
        existing_to_remove = [col for col in columns_to_remove if col in existing_columns]
        
        if existing_to_remove:
            logger.info(f"Need to remove columns: {existing_to_remove}")
            
            # SQLite doesn't support DROP COLUMN, so we need to recreate the table
            # First, get the current data
            cursor.execute("SELECT * FROM dataset_downloads")
            all_data = cursor.fetchall()
            
            # Get column names (excluding the ones we want to remove)
            cursor.execute("PRAGMA table_info(dataset_downloads)")
            all_columns_info = cursor.fetchall()
            keep_columns = [col[1] for col in all_columns_info if col[1] not in columns_to_remove]
            
            logger.info(f"Keeping columns: {keep_columns}")
            
            # Create new table with correct schema
            cursor.execute("DROP TABLE IF EXISTS dataset_downloads_new")
            
            create_table_sql = """
            CREATE TABLE dataset_downloads_new (
                id INTEGER PRIMARY KEY,
                dataset_id INTEGER NOT NULL,
                user_id INTEGER,
                download_token VARCHAR NOT NULL UNIQUE,
                file_format VARCHAR NOT NULL,
                compression VARCHAR,
                original_filename VARCHAR,
                file_size_bytes INTEGER,
                download_status VARCHAR DEFAULT 'pending',
                progress_percentage INTEGER DEFAULT 0,
                error_message TEXT,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                expires_at DATETIME,
                ip_address VARCHAR,
                user_agent VARCHAR,
                share_token VARCHAR,
                download_duration_seconds INTEGER,
                transfer_rate_mbps VARCHAR,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                organization_id INTEGER,
                FOREIGN KEY (dataset_id) REFERENCES datasets (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (organization_id) REFERENCES organizations (id)
            )
            """
            
            cursor.execute(create_table_sql)
            
            # Migrate data if there is any
            if all_data:
                # Map old data to new schema
                import uuid
                for row in all_data:
                    # Create a mapping of old row data
                    old_columns = [col[1] for col in all_columns_info]
                    row_dict = dict(zip(old_columns, row))
                    
                    # Generate download_token if not exists
                    if 'download_token' not in row_dict or not row_dict.get('download_token'):
                        row_dict['download_token'] = str(uuid.uuid4())
                    
                    # Set default values for new columns
                    row_dict.setdefault('download_status', 'completed')
                    row_dict.setdefault('progress_percentage', 100)
                    row_dict.setdefault('created_at', row_dict.get('started_at'))
                    row_dict.setdefault('updated_at', row_dict.get('completed_at') or row_dict.get('started_at'))
                    
                    # Convert duration_seconds to download_duration_seconds
                    if 'duration_seconds' in row_dict and row_dict['duration_seconds']:
                        row_dict['download_duration_seconds'] = int(float(row_dict['duration_seconds']))
                    
                    # Insert into new table
                    new_columns = [
                        'id', 'dataset_id', 'user_id', 'download_token', 'file_format', 
                        'compression', 'original_filename', 'file_size_bytes', 'download_status',
                        'progress_percentage', 'error_message', 'started_at', 'completed_at',
                        'expires_at', 'ip_address', 'user_agent', 'share_token',
                        'download_duration_seconds', 'transfer_rate_mbps', 'created_at',
                        'updated_at', 'organization_id'
                    ]
                    
                    values = []
                    for col in new_columns:
                        values.append(row_dict.get(col))
                    
                    placeholders = ','.join(['?' for _ in new_columns])
                    insert_sql = f"INSERT INTO dataset_downloads_new ({','.join(new_columns)}) VALUES ({placeholders})"
                    
                    cursor.execute(insert_sql, values)
            
            # Replace old table with new one
            cursor.execute("DROP TABLE dataset_downloads")
            cursor.execute("ALTER TABLE dataset_downloads_new RENAME TO dataset_downloads")
            
            logger.info("Table recreated with new schema")
        
        # Create index on download_token for performance
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_dataset_downloads_token ON dataset_downloads(download_token)")
        
        conn.commit()
        conn.close()
        
        logger.info("Dataset downloads migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_migration()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        exit(1)