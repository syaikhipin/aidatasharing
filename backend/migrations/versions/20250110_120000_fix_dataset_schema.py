#!/usr/bin/env python3
"""
Migration: Fix dataset schema and add missing columns
Created: 2025-01-10T12:00:00
Description: Fixes dataset table schema issues, adds missing columns, and ensures proper relationships
"""

import sqlite3
import logging
import json

logger = logging.getLogger(__name__)

def upgrade(cursor):
    """Apply the migration"""
    logger.info("Starting dataset schema fix migration...")
    
    # Check if datasets table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='datasets'")
    if not cursor.fetchone():
        logger.info("Datasets table doesn't exist, creating it...")
        create_datasets_table(cursor)
        return
    
    # Get current table structure
    cursor.execute("PRAGMA table_info(datasets)")
    existing_columns = {row[1]: row[2] for row in cursor.fetchall()}
    
    # Define required columns with their types
    required_columns = {
        'id': 'INTEGER',
        'name': 'VARCHAR',
        'description': 'TEXT',
        'file_path': 'VARCHAR',
        'file_type': 'VARCHAR',
        'file_size': 'INTEGER',
        'upload_date': 'DATETIME',
        'user_id': 'INTEGER',
        'organization_id': 'INTEGER',
        'department_id': 'INTEGER',
        'is_public': 'BOOLEAN',
        'sharing_level': 'VARCHAR',
        'tags': 'TEXT',
        'source_url': 'VARCHAR',
        'connector_id': 'INTEGER',
        'schema_info': 'JSON',
        'allow_download': 'BOOLEAN',
        'allow_api_access': 'BOOLEAN',
        'row_count': 'INTEGER',
        'column_count': 'INTEGER',
        'file_metadata': 'JSON',
        'content_preview': 'TEXT',
        'schema_metadata': 'JSON',
        'quality_metrics': 'JSON',
        'column_statistics': 'JSON',
        'preview_data': 'JSON',
        'download_count': 'INTEGER',
        'last_downloaded_at': 'DATETIME',
        'created_at': 'DATETIME',
        'updated_at': 'DATETIME',
        'deleted_at': 'DATETIME',
        'is_deleted': 'BOOLEAN',
        'deleted_by': 'INTEGER'
    }
    
    # Add missing columns
    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            logger.info(f"Adding missing column: {column_name}")
            try:
                if column_type == 'BOOLEAN':
                    cursor.execute(f"ALTER TABLE datasets ADD COLUMN {column_name} {column_type} DEFAULT 0")
                elif column_type == 'INTEGER':
                    cursor.execute(f"ALTER TABLE datasets ADD COLUMN {column_name} {column_type} DEFAULT 0")
                elif column_type == 'DATETIME':
                    cursor.execute(f"ALTER TABLE datasets ADD COLUMN {column_name} {column_type}")
                else:
                    cursor.execute(f"ALTER TABLE datasets ADD COLUMN {column_name} {column_type}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    logger.error(f"Failed to add column {column_name}: {e}")
                    raise
    
    # Fix dataset_models table
    fix_dataset_models_table(cursor)
    
    # Fix dataset_downloads table
    fix_dataset_downloads_table(cursor)
    
    # Create indexes for performance
    create_indexes(cursor)
    
    logger.info("Dataset schema fix migration completed successfully")

def create_datasets_table(cursor):
    """Create the datasets table from scratch"""
    cursor.execute("""
        CREATE TABLE datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR NOT NULL,
            description TEXT,
            file_path VARCHAR,
            file_type VARCHAR,
            file_size INTEGER DEFAULT 0,
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            organization_id INTEGER,
            department_id INTEGER,
            is_public BOOLEAN DEFAULT 0,
            sharing_level VARCHAR DEFAULT 'PRIVATE',
            tags TEXT,
            source_url VARCHAR,
            connector_id INTEGER,
            schema_info JSON,
            allow_download BOOLEAN DEFAULT 1,
            allow_api_access BOOLEAN DEFAULT 1,
            row_count INTEGER DEFAULT 0,
            column_count INTEGER DEFAULT 0,
            file_metadata JSON,
            content_preview TEXT,
            schema_metadata JSON,
            quality_metrics JSON,
            column_statistics JSON,
            preview_data JSON,
            download_count INTEGER DEFAULT 0,
            last_downloaded_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            deleted_at DATETIME,
            is_deleted BOOLEAN DEFAULT 0,
            deleted_by INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (organization_id) REFERENCES organizations (id),
            FOREIGN KEY (department_id) REFERENCES departments (id),
            FOREIGN KEY (connector_id) REFERENCES database_connectors (id),
            FOREIGN KEY (deleted_by) REFERENCES users (id)
        )
    """)

def fix_dataset_models_table(cursor):
    """Fix dataset_models table schema"""
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dataset_models'")
    if not cursor.fetchone():
        logger.info("Creating dataset_models table...")
        cursor.execute("""
            CREATE TABLE dataset_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                name VARCHAR NOT NULL,
                model_type VARCHAR NOT NULL,
                mindsdb_model_name VARCHAR NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_deleted BOOLEAN DEFAULT 0,
                deleted_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                ai_model_version VARCHAR,
                model_params JSON,
                training_status VARCHAR DEFAULT 'pending',
                accuracy_score REAL,
                FOREIGN KEY (dataset_id) REFERENCES datasets (id),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        """)
        return
    
    # Get current columns
    cursor.execute("PRAGMA table_info(dataset_models)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    # Add missing columns
    model_columns = {
        'ai_model_version': 'VARCHAR',
        'model_params': 'JSON',
        'training_status': 'VARCHAR',
        'accuracy_score': 'REAL',
        'created_by': 'INTEGER',
        'created_at': 'DATETIME',
        'updated_at': 'DATETIME'
    }
    
    for column_name, column_type in model_columns.items():
        if column_name not in existing_columns:
            logger.info(f"Adding column {column_name} to dataset_models")
            try:
                if column_name == 'training_status':
                    cursor.execute(f"ALTER TABLE dataset_models ADD COLUMN {column_name} {column_type} DEFAULT 'pending'")
                elif column_type == 'DATETIME':
                    cursor.execute(f"ALTER TABLE dataset_models ADD COLUMN {column_name} {column_type} DEFAULT CURRENT_TIMESTAMP")
                else:
                    cursor.execute(f"ALTER TABLE dataset_models ADD COLUMN {column_name} {column_type}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    logger.error(f"Failed to add column {column_name}: {e}")

def fix_dataset_downloads_table(cursor):
    """Fix dataset_downloads table schema"""
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dataset_downloads'")
    if not cursor.fetchone():
        logger.info("Creating dataset_downloads table...")
        cursor.execute("""
            CREATE TABLE dataset_downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                download_token VARCHAR UNIQUE NOT NULL,
                file_format VARCHAR DEFAULT 'csv',
                compression VARCHAR,
                original_filename VARCHAR,
                file_size_bytes INTEGER DEFAULT 0,
                download_status VARCHAR DEFAULT 'pending',
                progress_percentage INTEGER DEFAULT 0,
                error_message TEXT,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                expires_at DATETIME,
                ip_address VARCHAR,
                user_agent TEXT,
                share_token VARCHAR,
                download_duration_seconds REAL,
                transfer_rate_mbps REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                organization_id INTEGER,
                FOREIGN KEY (dataset_id) REFERENCES datasets (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (organization_id) REFERENCES organizations (id)
            )
        """)
        return
    
    # Get current columns
    cursor.execute("PRAGMA table_info(dataset_downloads)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    # Add missing columns
    download_columns = {
        'download_duration_seconds': 'REAL',
        'transfer_rate_mbps': 'REAL',
        'organization_id': 'INTEGER',
        'share_token': 'VARCHAR',
        'ip_address': 'VARCHAR',
        'user_agent': 'TEXT'
    }
    
    for column_name, column_type in download_columns.items():
        if column_name not in existing_columns:
            logger.info(f"Adding column {column_name} to dataset_downloads")
            try:
                cursor.execute(f"ALTER TABLE dataset_downloads ADD COLUMN {column_name} {column_type}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    logger.error(f"Failed to add column {column_name}: {e}")

def create_indexes(cursor):
    """Create indexes for better performance"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_datasets_user_id ON datasets(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_datasets_organization_id ON datasets(organization_id)",
        "CREATE INDEX IF NOT EXISTS idx_datasets_sharing_level ON datasets(sharing_level)",
        "CREATE INDEX IF NOT EXISTS idx_datasets_is_deleted ON datasets(is_deleted)",
        "CREATE INDEX IF NOT EXISTS idx_dataset_models_dataset_id ON dataset_models(dataset_id)",
        "CREATE INDEX IF NOT EXISTS idx_dataset_models_is_active ON dataset_models(is_active)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_dataset_downloads_token ON dataset_downloads(download_token)",
        "CREATE INDEX IF NOT EXISTS idx_dataset_downloads_dataset_id ON dataset_downloads(dataset_id)",
        "CREATE INDEX IF NOT EXISTS idx_dataset_downloads_status ON dataset_downloads(download_status)"
    ]
    
    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
        except sqlite3.OperationalError as e:
            if "already exists" not in str(e).lower():
                logger.error(f"Failed to create index: {e}")

def downgrade(cursor):
    """Rollback the migration (optional)"""
    logger.warning("Downgrade not implemented for dataset schema fix")
    pass