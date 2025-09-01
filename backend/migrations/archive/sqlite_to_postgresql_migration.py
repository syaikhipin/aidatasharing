#!/usr/bin/env python3
"""
Complete SQLite to PostgreSQL Migration Script
This script reads data from the existing SQLite database and migrates it to PostgreSQL.
Created: 2025-08-26
"""

import logging
import sqlite3
import os
import sys
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from urllib.parse import urlparse
import json

# Add the backend directory to the path so we can import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import Base
import app.models  # Import all models to register them with SQLAlchemy

logger = logging.getLogger(__name__)

class SQLiteToPostgreSQLMigration:
    """Complete migration from SQLite to PostgreSQL"""
    
    def __init__(self, sqlite_db_path: str, postgresql_url: str):
        self.sqlite_db_path = sqlite_db_path
        self.postgresql_url = postgresql_url
        self.pg_engine = create_engine(postgresql_url)
        
    def _get_sqlite_connection(self):
        """Get SQLite database connection"""
        if not os.path.exists(self.sqlite_db_path):
            raise FileNotFoundError(f"SQLite database not found at {self.sqlite_db_path}")
        return sqlite3.connect(self.sqlite_db_path)
    
    def _get_sqlite_tables(self, conn):
        """Get all tables from SQLite database"""
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        return [row[0] for row in cursor.fetchall()]
    
    def _get_table_schema(self, conn, table_name):
        """Get table schema from SQLite"""
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        return cursor.fetchall()
    
    def _get_table_data(self, conn, table_name):
        """Get all data from a SQLite table"""
        cursor = conn.execute(f"SELECT * FROM {table_name}")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        return columns, rows
    
    def _create_postgresql_schema(self):
        """Create PostgreSQL schema using SQLAlchemy models"""
        try:
            # Create all tables
            Base.metadata.create_all(bind=self.pg_engine)
            logger.info("PostgreSQL schema created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL schema: {e}")
            return False
    
    def _migrate_table_data(self, table_name, columns, rows):
        """Migrate data from SQLite table to PostgreSQL"""
        if not rows:
            logger.info(f"No data to migrate for table: {table_name}")
            return True
            
        try:
            with self.pg_engine.connect() as conn:
                # Handle different table types
                if table_name == 'users':
                    return self._migrate_users(conn, columns, rows)
                elif table_name == 'organizations':
                    return self._migrate_organizations(conn, columns, rows)
                elif table_name == 'datasets':
                    return self._migrate_datasets(conn, columns, rows)
                elif table_name == 'configurations':
                    return self._migrate_configurations(conn, columns, rows)
                elif table_name == 'database_connectors':
                    return self._migrate_database_connectors(conn, columns, rows)
                else:
                    # Generic migration for other tables
                    return self._migrate_generic_table(conn, table_name, columns, rows)
                    
        except Exception as e:
            logger.error(f"Failed to migrate table {table_name}: {e}")
            return False
    
    def _migrate_users(self, conn, columns, rows):
        """Migrate users table with proper boolean and column handling"""
        with conn.begin():  # Use transaction for batch insert
            for row in rows:
                row_dict = dict(zip(columns, row))
                
                # Convert SQLite integers to PostgreSQL booleans
                row_dict['is_active'] = bool(row_dict.get('is_active', 1))
                row_dict['is_superuser'] = bool(row_dict.get('is_superuser', 0))
                
                # Only include columns that exist in the PostgreSQL schema (excluding role for now)
                user_data = {
                    'id': row_dict.get('id'),
                    'email': row_dict.get('email'),
                    'hashed_password': row_dict.get('hashed_password'),
                    'full_name': row_dict.get('full_name'),
                    'is_active': row_dict['is_active'],
                    'is_superuser': row_dict['is_superuser'],
                    'organization_id': row_dict.get('organization_id'),
                    'created_at': row_dict.get('created_at'),
                    'updated_at': row_dict.get('updated_at')
                }
                
                try:
                    conn.execute(text("""
                        INSERT INTO users (id, email, hashed_password, full_name, is_active, 
                                         is_superuser, organization_id, created_at, updated_at)
                        VALUES (:id, :email, :hashed_password, :full_name, :is_active,
                               :is_superuser, :organization_id, :created_at, :updated_at)
                        ON CONFLICT (id) DO UPDATE SET
                            email = EXCLUDED.email,
                            hashed_password = EXCLUDED.hashed_password,
                            full_name = EXCLUDED.full_name,
                            is_active = EXCLUDED.is_active,
                            is_superuser = EXCLUDED.is_superuser,
                            organization_id = EXCLUDED.organization_id,
                            updated_at = EXCLUDED.updated_at
                    """), user_data)
                    
                except Exception as e:
                    logger.error(f"Error migrating user {row_dict.get('email', 'unknown')}: {e}")
                    continue
                    
        return True
    
    def _migrate_organizations(self, conn, columns, rows):
        """Migrate organizations table with boolean conversion"""
        with conn.begin():  # Use transaction for batch insert
            for row in rows:
                row_dict = dict(zip(columns, row))
                
                # Convert SQLite integers to PostgreSQL booleans
                row_dict['is_active'] = bool(row_dict.get('is_active', 1))
                row_dict['allow_external_sharing'] = bool(row_dict.get('allow_external_sharing', 0))
                
                try:
                    conn.execute(text("""
                        INSERT INTO organizations (id, name, slug, description, type, is_active,
                                                 allow_external_sharing, default_sharing_level,
                                                 website, contact_email, created_at, updated_at)
                        VALUES (:id, :name, :slug, :description, :type, :is_active,
                               :allow_external_sharing, :default_sharing_level,
                               :website, :contact_email, :created_at, :updated_at)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            slug = EXCLUDED.slug,
                            description = EXCLUDED.description,
                            type = EXCLUDED.type,
                            is_active = EXCLUDED.is_active,
                            allow_external_sharing = EXCLUDED.allow_external_sharing,
                            default_sharing_level = EXCLUDED.default_sharing_level,
                            website = EXCLUDED.website,
                            contact_email = EXCLUDED.contact_email,
                            updated_at = EXCLUDED.updated_at
                    """), row_dict)
                    
                except Exception as e:
                    logger.error(f"Error migrating organization {row_dict.get('name', 'unknown')}: {e}")
                    continue
                    
        return True
    
    def _migrate_datasets(self, conn, columns, rows):
        """Migrate datasets table with proper boolean and JSON field handling"""
        with conn.begin():  # Use transaction for batch insert
            for row in rows:
                row_dict = dict(zip(columns, row))
                
                # Convert SQLite integers to PostgreSQL booleans
                bool_fields = ['is_active', 'is_deleted', 'public_share_enabled', 'ai_chat_enabled',
                              'allow_download', 'allow_api_access', 'allow_ai_chat', 'allow_model_training',
                              'is_public', 'is_multi_file_dataset']
                for field in bool_fields:
                    if field in row_dict and isinstance(row_dict[field], (int, str)) and str(row_dict[field]).isdigit():
                        row_dict[field] = bool(int(row_dict[field]))
                
                # Handle JSON fields
                json_fields = ['connection_params', 'schema_info', 'file_metadata', 'ai_insights', 
                              'ai_recommendations', 'chat_context', 'preview_data', 'schema_metadata',
                              'quality_metrics', 'column_statistics', 'files_metadata', 'tags']
                
                for field in json_fields:
                    if field in row_dict and row_dict[field]:
                        try:
                            # If it's already a dict/list, convert to JSON string
                            if isinstance(row_dict[field], (dict, list)):
                                row_dict[field] = json.dumps(row_dict[field])
                            elif isinstance(row_dict[field], str):
                                # Verify it's valid JSON
                                json.loads(row_dict[field])
                        except:
                            row_dict[field] = None
                
                try:
                    # Filter columns to match PostgreSQL schema
                    pg_columns = [
                        'id', 'name', 'description', 'type', 'status', 'is_active', 'is_deleted', 
                        'deleted_at', 'deleted_by', 'source_url', 'connection_params', 'connector_id',
                        'is_multi_file_dataset', 'primary_file_path', 'owner_id', 'organization_id', 
                        'sharing_level', 'size_bytes', 'row_count', 'column_count', 'schema_info',
                        'file_metadata', 'content_preview', 'mindsdb_table_name', 'mindsdb_database',
                        'ai_processing_status', 'ai_summary', 'ai_insights', 'ai_recommendations',
                        'public_share_enabled', 'share_token', 'share_password', 'share_view_count',
                        'ai_chat_enabled', 'chat_model_name', 'chat_context', 'allow_download',
                        'allow_api_access', 'allow_ai_chat', 'allow_model_training', 'data_quality_score',
                        'completeness_score', 'consistency_score', 'accuracy_score', 'file_path',
                        'preview_data', 'schema_metadata', 'quality_metrics', 'column_statistics',
                        'files_metadata', 'total_files_count', 'download_count', 'last_downloaded_at',
                        'created_at', 'updated_at', 'last_accessed', 'ai_processed_at'
                    ]
                    
                    available_columns = [col for col in pg_columns if col in row_dict]
                    if not available_columns:
                        logger.warning(f"No matching columns for dataset {row_dict.get('name', 'unknown')}")
                        continue
                    
                    placeholders = ', '.join([f":{col}" for col in available_columns])
                    column_names = ', '.join(available_columns)
                    
                    # Update clauses for conflict resolution
                    update_clauses = ', '.join([f"{col} = EXCLUDED.{col}" for col in available_columns if col != 'id'])
                    
                    query = f"""
                        INSERT INTO datasets ({column_names})
                        VALUES ({placeholders})
                        ON CONFLICT (id) DO UPDATE SET
                            {update_clauses}
                    """
                    
                    dataset_data = {col: row_dict[col] for col in available_columns}
                    conn.execute(text(query), dataset_data)
                    
                except Exception as e:
                    logger.error(f"Error migrating dataset {row_dict.get('name', 'unknown')}: {e}")
                    continue
                    
        return True
    
    def _migrate_configurations(self, conn, columns, rows):
        """Migrate configurations table with schema compatibility"""
        with conn.begin():  # Use transaction for batch insert
            for row in rows:
                row_dict = dict(zip(columns, row))
                
                # Convert boolean fields
                if 'is_sensitive' in row_dict and isinstance(row_dict['is_sensitive'], (int, str)):
                    row_dict['is_sensitive'] = bool(int(row_dict.get('is_sensitive', 0)))
                
                try:
                    # Only use columns that exist in both SQLite and PostgreSQL
                    config_data = {
                        'key': row_dict.get('key'),
                        'value': row_dict.get('value'),
                        'description': row_dict.get('description'),
                        'created_at': row_dict.get('created_at'),
                        'updated_at': row_dict.get('updated_at')
                    }
                    
                    # Filter out None values
                    config_data = {k: v for k, v in config_data.items() if v is not None}
                    
                    if not config_data.get('key'):
                        continue
                    
                    placeholders = ', '.join([f":{col}" for col in config_data.keys()])
                    column_names = ', '.join(config_data.keys())
                    update_clauses = ', '.join([f"{col} = EXCLUDED.{col}" for col in config_data.keys() if col != 'key'])
                    
                    query = f"""
                        INSERT INTO configurations ({column_names})
                        VALUES ({placeholders})
                        ON CONFLICT (key) DO UPDATE SET
                            {update_clauses}
                    """
                    
                    conn.execute(text(query), config_data)
                    
                except Exception as e:
                    logger.error(f"Error migrating configuration {row_dict.get('key', 'unknown')}: {e}")
                    continue
                    
        return True
    
    def _migrate_database_connectors(self, conn, columns, rows):
        """Migrate database connectors table with boolean conversion"""
        with conn.begin():  # Use transaction for batch insert
            for row in rows:
                row_dict = dict(zip(columns, row))
                
                # Convert SQLite integers to PostgreSQL booleans
                bool_fields = ['is_active', 'is_deleted', 'is_editable', 'supports_write', 
                              'supports_real_time', 'auto_sync_enabled']
                for field in bool_fields:
                    if field in row_dict:
                        row_dict[field] = bool(row_dict[field])
                
                # Handle JSON fields
                json_fields = ['connection_config', 'credentials']
                for field in json_fields:
                    if field in row_dict and row_dict[field]:
                        try:
                            if isinstance(row_dict[field], (dict, list)):
                                row_dict[field] = json.dumps(row_dict[field])
                            elif isinstance(row_dict[field], str):
                                json.loads(row_dict[field])
                        except:
                            row_dict[field] = None
                
                try:
                    available_columns = [col for col in columns if col in row_dict]
                    placeholders = ', '.join([f":{col}" for col in available_columns])
                    column_names = ', '.join(available_columns)
                    update_clauses = ', '.join([f"{col} = EXCLUDED.{col}" for col in available_columns if col != 'id'])
                    
                    query = f"""
                        INSERT INTO database_connectors ({column_names})
                        VALUES ({placeholders})
                        ON CONFLICT (id) DO UPDATE SET
                            {update_clauses}
                    """
                    
                    conn.execute(text(query), {col: row_dict[col] for col in available_columns})
                    
                except Exception as e:
                    logger.error(f"Error migrating database connector {row_dict.get('name', 'unknown')}: {e}")
                    continue
                    
        return True
    
    def _migrate_generic_table(self, conn, table_name, columns, rows):
        """Generic migration for other tables with boolean handling"""
        logger.info(f"Attempting generic migration for table: {table_name}")
        
        with conn.begin():  # Use transaction for batch insert
            for row in rows:
                row_dict = dict(zip(columns, row))
                
                try:
                    # Convert common boolean fields
                    bool_fields = ['is_active', 'is_deleted', 'is_primary', 'is_processed', 'is_sensitive', 
                                  'allow_download', 'allow_api_access', 'allow_ai_chat', 'allow_model_training', 
                                  'public_share_enabled', 'ai_chat_enabled', 'is_multi_file_dataset', 'is_read',
                                  'is_public', 'is_editable', 'supports_write', 'supports_real_time', 'auto_sync_enabled']
                    for field in bool_fields:
                        if field in row_dict and isinstance(row_dict[field], (int, str)) and str(row_dict[field]).isdigit():
                            row_dict[field] = bool(int(row_dict[field]))
                    
                    # Try to detect JSON columns and handle them
                    for key, value in row_dict.items():
                        if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                            try:
                                json.loads(value)
                                # It's valid JSON, keep as is
                            except:
                                # Not valid JSON, keep as string
                                pass
                    
                    available_columns = [col for col in columns if col in row_dict and row_dict[col] is not None]
                    if not available_columns:
                        continue
                        
                    placeholders = ', '.join([f":{col}" for col in available_columns])
                    column_names = ', '.join(available_columns)
                    
                    # Simple insert with conflict ignore for generic tables
                    query = f"""
                        INSERT INTO {table_name} ({column_names})
                        VALUES ({placeholders})
                        ON CONFLICT DO NOTHING
                    """
                    
                    conn.execute(text(query), {col: row_dict[col] for col in available_columns})
                    
                except Exception as e:
                    logger.warning(f"Error migrating row in {table_name}: {e}")
                    continue
                    
        return True
    
    def _update_sequences(self):
        """Update PostgreSQL sequences to match the migrated data"""
        try:
            with self.pg_engine.connect() as conn:
                # Get all tables with SERIAL columns
                result = conn.execute(text("""
                    SELECT schemaname, tablename, columnname, sequencename
                    FROM pg_sequences
                    WHERE schemaname = 'public'
                """))
                
                for row in result:
                    table_name = row[1]
                    sequence_name = row[3]
                    
                    try:
                        # Get the maximum ID from the table
                        max_id_result = conn.execute(text(f"SELECT MAX(id) FROM {table_name}"))
                        max_id = max_id_result.scalar()
                        
                        if max_id is not None:
                            # Update the sequence
                            conn.execute(text(f"SELECT setval('{sequence_name}', {max_id})"))
                            logger.info(f"Updated sequence {sequence_name} to {max_id}")
                    except Exception as e:
                        logger.warning(f"Could not update sequence for {table_name}: {e}")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating sequences: {e}")
    
    def run_migration(self):
        """Run the complete migration"""
        try:
            logger.info("Starting SQLite to PostgreSQL migration...")
            
            # Step 1: Create PostgreSQL schema
            logger.info("Creating PostgreSQL schema...")
            if not self._create_postgresql_schema():
                return False
            
            # Step 2: Connect to SQLite and get tables
            logger.info("Reading SQLite database...")
            with self._get_sqlite_connection() as sqlite_conn:
                tables = self._get_sqlite_tables(sqlite_conn)
                logger.info(f"Found tables: {tables}")
                
                # Step 3: Migrate each table
                for table_name in tables:
                    logger.info(f"Migrating table: {table_name}")
                    columns, rows = self._get_table_data(sqlite_conn, table_name)
                    logger.info(f"Table {table_name} has {len(rows)} rows")
                    
                    if not self._migrate_table_data(table_name, columns, rows):
                        logger.warning(f"Failed to migrate table {table_name}, continuing...")
                    else:
                        logger.info(f"Successfully migrated table: {table_name}")
            
            # Step 4: Update sequences
            logger.info("Updating PostgreSQL sequences...")
            self._update_sequences()
            
            logger.info("Migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

def main():
    """Main migration function"""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get database paths
    sqlite_db_path = "/Users/syaikhipin/Documents/program/simpleaisharing/storage/aishare_platform.db"
    postgresql_url = settings.DATABASE_URL
    
    if not os.path.exists(sqlite_db_path):
        logger.error(f"SQLite database not found at {sqlite_db_path}")
        return False
        
    if not postgresql_url.startswith('postgresql://'):
        logger.error("DATABASE_URL must be a PostgreSQL connection string")
        return False
    
    # Run migration
    migration = SQLiteToPostgreSQLMigration(sqlite_db_path, postgresql_url)
    success = migration.run_migration()
    
    if success:
        print("✅ Migration completed successfully!")
        print("Your SQLite data has been migrated to PostgreSQL.")
        print("You can now use the PostgreSQL database for your application.")
    else:
        print("❌ Migration failed!")
        return False
        
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)