#!/usr/bin/env python3
"""
PostgreSQL Consolidated Database Migration
This migration creates all tables to match the current schema state for PostgreSQL.
Created: 2025-08-26
"""

import logging
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class PostgreSQLConsolidatedMigration:
    """Consolidated migration that creates all tables matching current schema for PostgreSQL"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        
    def _create_users_table(self, conn):
        """Create users table"""
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR NOT NULL UNIQUE,
                hashed_password VARCHAR NOT NULL,
                full_name VARCHAR,
                is_active BOOLEAN DEFAULT TRUE,
                is_superuser BOOLEAN DEFAULT FALSE,
                organization_id INTEGER,
                role VARCHAR DEFAULT 'member',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_id ON users (id)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
        
    def _create_organizations_table(self, conn):
        """Create organizations table"""
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS organizations (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL UNIQUE,
                slug VARCHAR NOT NULL UNIQUE,
                description TEXT,
                type VARCHAR(14) DEFAULT 'business',
                is_active BOOLEAN DEFAULT TRUE,
                allow_external_sharing BOOLEAN DEFAULT FALSE,
                default_sharing_level VARCHAR(12) DEFAULT 'private',
                website VARCHAR,
                contact_email VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_organizations_id ON organizations (id)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_organizations_name ON organizations (name)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_organizations_slug ON organizations (slug)"))
        
    def _create_datasets_table(self, conn):
        """Create datasets table with all current columns"""
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS datasets (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                description TEXT,
                type VARCHAR NOT NULL,
                status VARCHAR DEFAULT 'active',
                is_active BOOLEAN DEFAULT TRUE,
                is_deleted BOOLEAN DEFAULT FALSE,
                deleted_at TIMESTAMP,
                deleted_by INTEGER,
                source_url VARCHAR,
                connection_params JSONB,
                connector_id INTEGER,
                is_multi_file_dataset BOOLEAN DEFAULT FALSE,
                primary_file_path VARCHAR,
                owner_id INTEGER NOT NULL,
                organization_id INTEGER NOT NULL,
                sharing_level VARCHAR DEFAULT 'private',
                size_bytes INTEGER,
                row_count INTEGER,
                column_count INTEGER,
                schema_info JSONB,
                file_metadata JSONB,
                content_preview TEXT,
                mindsdb_table_name VARCHAR,
                mindsdb_database VARCHAR,
                ai_processing_status VARCHAR DEFAULT 'not_processed',
                ai_summary TEXT,
                ai_insights JSONB,
                ai_recommendations JSONB,
                public_share_enabled BOOLEAN DEFAULT FALSE,
                share_token VARCHAR UNIQUE,
                share_password VARCHAR,
                share_view_count INTEGER DEFAULT 0,
                ai_chat_enabled BOOLEAN DEFAULT TRUE,
                chat_model_name VARCHAR,
                chat_context JSONB,
                allow_download BOOLEAN DEFAULT TRUE,
                allow_api_access BOOLEAN DEFAULT TRUE,
                allow_ai_chat BOOLEAN DEFAULT TRUE,
                allow_model_training BOOLEAN DEFAULT TRUE,
                data_quality_score VARCHAR,
                completeness_score VARCHAR,
                consistency_score VARCHAR,
                accuracy_score VARCHAR,
                file_path VARCHAR,
                preview_data JSONB,
                schema_metadata JSONB,
                quality_metrics JSONB,
                column_statistics JSONB,
                files_metadata JSONB,
                total_files_count INTEGER DEFAULT 1,
                download_count INTEGER DEFAULT 0,
                last_downloaded_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP,
                ai_processed_at TIMESTAMP
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_datasets_id ON datasets (id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_datasets_name ON datasets (name)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_datasets_is_active ON datasets (is_active)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_datasets_is_deleted ON datasets (is_deleted)"))
        
    def _create_dataset_files_table(self, conn):
        """Create dataset_files table"""
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dataset_files (
                id SERIAL PRIMARY KEY,
                dataset_id INTEGER NOT NULL,
                filename VARCHAR NOT NULL,
                file_path VARCHAR NOT NULL,
                relative_path VARCHAR,
                file_size INTEGER,
                file_type VARCHAR,
                mime_type VARCHAR,
                file_metadata JSONB,
                is_primary BOOLEAN DEFAULT FALSE,
                file_order INTEGER DEFAULT 0,
                is_processed BOOLEAN DEFAULT FALSE,
                is_deleted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_dataset_files_id ON dataset_files (id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_dataset_files_dataset_id ON dataset_files (dataset_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_dataset_files_is_primary ON dataset_files (is_primary)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_dataset_files_is_deleted ON dataset_files (is_deleted)"))
        
    def _create_foreign_keys(self, conn):
        """Add foreign key constraints (PostgreSQL supports adding them after table creation)"""
        try:
            # Users -> Organizations
            conn.execute(text("""
                ALTER TABLE users 
                ADD CONSTRAINT fk_users_organization_id 
                FOREIGN KEY (organization_id) REFERENCES organizations(id)
            """))
        except Exception:
            # Constraint might already exist
            pass
            
        try:
            # Datasets -> Users (owner_id)
            conn.execute(text("""
                ALTER TABLE datasets 
                ADD CONSTRAINT fk_datasets_owner_id 
                FOREIGN KEY (owner_id) REFERENCES users(id)
            """))
        except Exception:
            pass
            
        try:
            # Datasets -> Organizations
            conn.execute(text("""
                ALTER TABLE datasets 
                ADD CONSTRAINT fk_datasets_organization_id 
                FOREIGN KEY (organization_id) REFERENCES organizations(id)
            """))
        except Exception:
            pass
            
        try:
            # Dataset files -> Datasets
            conn.execute(text("""
                ALTER TABLE dataset_files 
                ADD CONSTRAINT fk_dataset_files_dataset_id 
                FOREIGN KEY (dataset_id) REFERENCES datasets(id)
            """))
        except Exception:
            pass
            
    def _create_additional_tables(self, conn):
        """Create additional tables needed by the application"""
        
        # Schema migrations table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                version VARCHAR(255) UNIQUE NOT NULL,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                checksum VARCHAR(255),
                migration_type VARCHAR(50) DEFAULT 'individual'
            )
        """))
        
        # Configurations table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS configurations (
                id SERIAL PRIMARY KEY,
                key VARCHAR NOT NULL UNIQUE,
                value TEXT,
                value_type VARCHAR DEFAULT 'string',
                description TEXT,
                category VARCHAR DEFAULT 'general',
                is_sensitive BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Database connectors table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS database_connectors (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                connector_type VARCHAR NOT NULL,
                organization_id INTEGER NOT NULL,
                connection_config JSONB NOT NULL,
                credentials JSONB,
                is_active BOOLEAN DEFAULT TRUE,
                is_deleted BOOLEAN DEFAULT FALSE,
                deleted_at TIMESTAMP,
                deleted_by INTEGER,
                mindsdb_database_name VARCHAR,
                description TEXT,
                created_by INTEGER NOT NULL,
                last_tested_at TIMESTAMP,
                test_status VARCHAR DEFAULT 'untested',
                test_error TEXT,
                is_editable BOOLEAN DEFAULT TRUE,
                supports_write BOOLEAN DEFAULT FALSE,
                max_connections INTEGER DEFAULT 5,
                connection_timeout INTEGER DEFAULT 30,
                supports_real_time BOOLEAN DEFAULT FALSE,
                last_synced_at TIMESTAMP,
                sync_frequency INTEGER DEFAULT 3600,
                auto_sync_enabled BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
    def _insert_initial_data(self, conn):
        """Insert initial system data"""
        # Insert default organizations matching init_db.py
        default_orgs = [
            ('System Administration', 'system-admin', 'Default organization for system administrators', 'enterprise'),
            ('Demo Organization', 'demo-org', 'A demo organization for testing purposes', 'small_business'),
            ('Open Source Community', 'open-source', 'Community for open source projects', 'nonprofit')
        ]
        
        for org_data in default_orgs:
            conn.execute(text("""
                INSERT INTO organizations (name, slug, description, type, is_active) 
                VALUES (:name, :slug, :description, :type, TRUE)
                ON CONFLICT (name) DO NOTHING
            """), {
                'name': org_data[0],
                'slug': org_data[1],
                'description': org_data[2],
                'type': org_data[3]
            })
        
        # Insert default configurations
        configs = [
            ('app_name', 'AI Share Platform', 'string', 'Application name', 'general', False),
            ('maintenance_mode', 'false', 'boolean', 'Maintenance mode status', 'system', False),
            ('max_file_size_mb', '100', 'integer', 'Maximum file upload size in MB', 'upload', False),
            ('allowed_file_types', 'csv,json,xlsx,txt,pdf,docx', 'string', 'Allowed file types for upload', 'upload', False),
            ('default_ai_model', 'gemini-2.0-flash', 'string', 'Default AI model for chat', 'ai', False),
            ('google_api_key', None, 'string', 'Google API key for Gemini Flash integration', 'ai', True),
            ('mindsdb_url', 'http://localhost:47334', 'string', 'MindsDB server URL', 'services', False)
        ]
        
        for config in configs:
            conn.execute(text("""
                INSERT INTO configurations (key, value, value_type, description, category, is_sensitive) 
                VALUES (:key, :value, :value_type, :description, :category, :is_sensitive)
                ON CONFLICT (key) DO NOTHING
            """), {
                'key': config[0],
                'value': config[1], 
                'value_type': config[2],
                'description': config[3],
                'category': config[4],
                'is_sensitive': config[5]
            })
        
    def run_migration(self):
        """Run the full migration"""
        try:
            with self.engine.connect() as conn:
                with conn.begin():  # Start transaction
                    logger.info("Creating organizations table...")
                    self._create_organizations_table(conn)
                    
                    logger.info("Creating users table...")
                    self._create_users_table(conn)
                    
                    logger.info("Creating datasets table...")
                    self._create_datasets_table(conn)
                    
                    logger.info("Creating dataset_files table...")
                    self._create_dataset_files_table(conn)
                    
                    logger.info("Creating additional tables...")
                    self._create_additional_tables(conn)
                    
                    logger.info("Adding foreign key constraints...")
                    self._create_foreign_keys(conn)
                    
                    logger.info("Inserting initial data...")
                    self._insert_initial_data(conn)
                    
                    # Mark migration as applied
                    conn.execute(text("""
                        INSERT INTO schema_migrations (version, description, migration_type) 
                        VALUES ('consolidated_postgresql_v1', 'PostgreSQL consolidated migration - all tables and initial data', 'consolidated')
                        ON CONFLICT (version) DO NOTHING
                    """))
                    
                    logger.info("PostgreSQL migration completed successfully!")
                    return True
                    
        except Exception as e:
            logger.error(f"PostgreSQL migration failed: {e}")
            return False

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        exit(1)
        
    if not database_url.startswith('postgresql://'):
        print("ERROR: DATABASE_URL must be a PostgreSQL connection string")
        exit(1)
    
    migration = PostgreSQLConsolidatedMigration(database_url)
    success = migration.run_migration()
    
    if success:
        print("✅ PostgreSQL migration completed successfully!")
    else:
        print("❌ PostgreSQL migration failed!")
        exit(1)