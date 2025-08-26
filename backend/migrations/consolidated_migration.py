#!/usr/bin/env python3
"""
Consolidated Database Migration
This migration creates all tables to match the current schema state.
Created: 2025-08-26
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class ConsolidatedMigration:
    """Consolidated migration that creates all tables matching current schema"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.database_path = Path(database_url.replace('sqlite:///', ''))
        
    def _create_users_table(self, cursor):
        """Create users table"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR NOT NULL UNIQUE,
                email VARCHAR NOT NULL UNIQUE,
                full_name VARCHAR,
                hashed_password VARCHAR NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_superuser BOOLEAN DEFAULT 0,
                is_admin BOOLEAN DEFAULT 0,
                organization_id INTEGER,
                last_login DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(organization_id) REFERENCES organizations(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_id ON users (id)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)")
        
    def _create_organizations_table(self, cursor):
        """Create organizations table"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR NOT NULL UNIQUE,
                slug VARCHAR NOT NULL UNIQUE,
                description TEXT,
                type VARCHAR(14) DEFAULT 'business',
                is_active BOOLEAN DEFAULT 1,
                allow_external_sharing BOOLEAN DEFAULT 0,
                default_sharing_level VARCHAR(12) DEFAULT 'private',
                website VARCHAR,
                contact_email VARCHAR,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_organizations_id ON organizations (id)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_organizations_name ON organizations (name)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_organizations_slug ON organizations (slug)")
        
    def _create_datasets_table(self, cursor):
        """Create datasets table with all current columns"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR NOT NULL,
                description TEXT,
                type VARCHAR NOT NULL,
                status VARCHAR DEFAULT 'active',
                is_active BOOLEAN DEFAULT 1,
                is_deleted BOOLEAN DEFAULT 0,
                deleted_at DATETIME,
                deleted_by INTEGER,
                source_url VARCHAR,
                connection_params JSON,
                connector_id INTEGER,
                is_multi_file_dataset BOOLEAN DEFAULT 0,
                primary_file_path VARCHAR,
                owner_id INTEGER NOT NULL,
                organization_id INTEGER NOT NULL,
                sharing_level VARCHAR DEFAULT 'private',
                size_bytes INTEGER,
                row_count INTEGER,
                column_count INTEGER,
                schema_info JSON,
                file_metadata JSON,
                content_preview TEXT,
                mindsdb_table_name VARCHAR,
                mindsdb_database VARCHAR,
                ai_processing_status VARCHAR DEFAULT 'not_processed',
                ai_summary TEXT,
                ai_insights JSON,
                ai_recommendations JSON,
                public_share_enabled BOOLEAN DEFAULT 0,
                share_token VARCHAR UNIQUE,
                share_password VARCHAR,
                share_view_count INTEGER DEFAULT 0,
                ai_chat_enabled BOOLEAN DEFAULT 1,
                chat_model_name VARCHAR,
                chat_context JSON,
                allow_download BOOLEAN DEFAULT 1,
                allow_api_access BOOLEAN DEFAULT 1,
                allow_ai_chat BOOLEAN DEFAULT 1,
                allow_model_training BOOLEAN DEFAULT 1,
                data_quality_score VARCHAR,
                completeness_score VARCHAR,
                consistency_score VARCHAR,
                accuracy_score VARCHAR,
                file_path VARCHAR,
                preview_data JSON,
                schema_metadata JSON,
                quality_metrics JSON,
                column_statistics JSON,
                files_metadata JSON,
                total_files_count INTEGER DEFAULT 1,
                download_count INTEGER DEFAULT 0,
                last_downloaded_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_accessed DATETIME,
                ai_processed_at DATETIME,
                FOREIGN KEY(owner_id) REFERENCES users(id),
                FOREIGN KEY(organization_id) REFERENCES organizations(id),
                FOREIGN KEY(connector_id) REFERENCES database_connectors(id),
                FOREIGN KEY(deleted_by) REFERENCES users(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_datasets_id ON datasets (id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_datasets_name ON datasets (name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_datasets_is_active ON datasets (is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_datasets_is_deleted ON datasets (is_deleted)")
        
    def _create_dataset_files_table(self, cursor):
        """Create dataset_files table"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dataset_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                filename VARCHAR NOT NULL,
                file_path VARCHAR NOT NULL,
                relative_path VARCHAR,
                file_size INTEGER,
                file_type VARCHAR,
                mime_type VARCHAR,
                file_metadata JSON,
                is_primary BOOLEAN DEFAULT 0,
                file_order INTEGER DEFAULT 0,
                is_processed BOOLEAN DEFAULT 0,
                is_deleted BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(dataset_id) REFERENCES datasets(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dataset_files_id ON dataset_files (id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dataset_files_dataset_id ON dataset_files (dataset_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dataset_files_is_primary ON dataset_files (is_primary)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dataset_files_is_deleted ON dataset_files (is_deleted)")
        
    def _create_models_table(self, cursor):
        """Create dataset models table"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dataset_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                name VARCHAR NOT NULL,
                model_type VARCHAR NOT NULL,
                mindsdb_model_name VARCHAR NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_deleted BOOLEAN DEFAULT 0,
                deleted_at DATETIME,
                deleted_by INTEGER,
                target_column VARCHAR,
                feature_columns JSON,
                model_params JSON,
                engine_type VARCHAR,
                ai_model_version VARCHAR,
                accuracy VARCHAR,
                training_time INTEGER,
                prediction_count INTEGER DEFAULT 0,
                last_prediction_at DATETIME,
                status VARCHAR DEFAULT 'training',
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(dataset_id) REFERENCES datasets(id),
                FOREIGN KEY(deleted_by) REFERENCES users(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dataset_models_id ON dataset_models (id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dataset_models_dataset_id ON dataset_models (dataset_id)")
        
    def _create_file_uploads_table(self, cursor):
        """Create file uploads table"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename VARCHAR NOT NULL,
                file_path VARCHAR NOT NULL,
                file_size INTEGER,
                mime_type VARCHAR,
                upload_status VARCHAR DEFAULT 'pending',
                user_id INTEGER NOT NULL,
                organization_id INTEGER NOT NULL,
                dataset_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(organization_id) REFERENCES organizations(id),
                FOREIGN KEY(dataset_id) REFERENCES datasets(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_file_uploads_id ON file_uploads (id)")
        
    def _create_data_connectors_table(self, cursor):
        """Create database connectors table"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS database_connectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR NOT NULL,
                connector_type VARCHAR NOT NULL,
                organization_id INTEGER NOT NULL,
                connection_config JSON NOT NULL,
                credentials JSON,
                is_active BOOLEAN DEFAULT 1,
                is_deleted BOOLEAN DEFAULT 0,
                deleted_at DATETIME,
                deleted_by INTEGER,
                mindsdb_database_name VARCHAR,
                description TEXT,
                created_by INTEGER NOT NULL,
                last_tested_at DATETIME,
                test_status VARCHAR DEFAULT 'untested',
                test_error TEXT,
                is_editable BOOLEAN DEFAULT 1,
                supports_write BOOLEAN DEFAULT 0,
                max_connections INTEGER DEFAULT 5,
                connection_timeout INTEGER DEFAULT 30,
                supports_real_time BOOLEAN DEFAULT 0,
                last_synced_at DATETIME,
                sync_frequency INTEGER DEFAULT 3600,
                auto_sync_enabled BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(organization_id) REFERENCES organizations(id),
                FOREIGN KEY(created_by) REFERENCES users(id),
                FOREIGN KEY(deleted_by) REFERENCES users(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_database_connectors_id ON database_connectors (id)")
        
    def _create_proxy_connectors_table(self, cursor):
        """Create proxy connectors table"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proxy_connectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR NOT NULL,
                connector_type VARCHAR NOT NULL,
                organization_id INTEGER NOT NULL,
                target_url VARCHAR NOT NULL,
                api_key VARCHAR,
                headers JSON,
                auth_config JSON,
                is_active BOOLEAN DEFAULT 1,
                created_by INTEGER NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(organization_id) REFERENCES organizations(id),
                FOREIGN KEY(created_by) REFERENCES users(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_proxy_connectors_id ON proxy_connectors (id)")
        
    def _create_shared_proxy_links_table(self, cursor):
        """Create shared proxy links table"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shared_proxy_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proxy_connector_id INTEGER NOT NULL,
                share_token VARCHAR NOT NULL UNIQUE,
                share_name VARCHAR NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                password_protected BOOLEAN DEFAULT 0,
                password_hash VARCHAR,
                expires_at DATETIME,
                access_count INTEGER DEFAULT 0,
                max_access_count INTEGER,
                created_by INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(proxy_connector_id) REFERENCES proxy_connectors(id),
                FOREIGN KEY(created_by) REFERENCES users(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_shared_proxy_links_id ON shared_proxy_links (id)")
        
    def _create_shared_datasets_table(self, cursor):
        """Create shared datasets table"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dataset_access (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                user_id INTEGER,
                access_type VARCHAR NOT NULL,
                access_token VARCHAR,
                expires_at DATETIME,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(dataset_id) REFERENCES datasets(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dataset_access_id ON dataset_access (id)")
        
    def _create_chat_sessions_table(self, cursor):
        """Create dataset chat sessions table"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dataset_chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                user_id INTEGER,
                session_token VARCHAR NOT NULL UNIQUE,
                share_token VARCHAR,
                ip_address VARCHAR,
                user_agent VARCHAR,
                ai_model_name VARCHAR NOT NULL,
                system_prompt TEXT,
                context_data JSON,
                message_count INTEGER DEFAULT 0,
                total_tokens_used INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                ended_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(dataset_id) REFERENCES datasets(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dataset_chat_sessions_id ON dataset_chat_sessions (id)")
        
    def _create_chat_messages_table(self, cursor):
        """Create chat messages table"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                message_type VARCHAR NOT NULL,
                content TEXT NOT NULL,
                message_metadata JSON,
                tokens_used INTEGER,
                processing_time_ms INTEGER,
                ai_model_version VARCHAR,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES dataset_chat_sessions(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_chat_messages_id ON chat_messages (id)")
        
    def _create_access_requests_table(self, cursor):
        """Create access requests table"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                organization_id INTEGER NOT NULL,
                request_type VARCHAR NOT NULL,
                status VARCHAR DEFAULT 'pending',
                message TEXT,
                response_message TEXT,
                reviewed_by INTEGER,
                reviewed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(organization_id) REFERENCES organizations(id),
                FOREIGN KEY(reviewed_by) REFERENCES users(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_access_requests_id ON access_requests (id)")
        
    def _create_notifications_table(self, cursor):
        """Create notifications table"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type VARCHAR NOT NULL,
                title VARCHAR NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                data JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                read_at DATETIME,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_notifications_id ON notifications (id)")
        
    def _create_audit_logs_table(self, cursor):
        """Create audit logs table"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action VARCHAR NOT NULL,
                resource_type VARCHAR NOT NULL,
                resource_id INTEGER,
                details JSON,
                ip_address VARCHAR,
                user_agent VARCHAR,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_id ON audit_logs (id)")
        
    def _create_analytics_table(self, cursor):
        """Create analytics table"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER NOT NULL,
                metric_name VARCHAR NOT NULL,
                metric_value VARCHAR NOT NULL,
                date_recorded DATE NOT NULL,
                metadata JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(organization_id) REFERENCES organizations(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_usage_stats_id ON usage_stats (id)")
        
    def _create_admin_config_table(self, cursor):
        """Create admin configuration table"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configurations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key VARCHAR NOT NULL UNIQUE,
                value TEXT,
                value_type VARCHAR DEFAULT 'string',
                description TEXT,
                category VARCHAR DEFAULT 'general',
                is_sensitive BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_configurations_id ON configurations (id)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_configurations_key ON configurations (key)")
        
    def _create_indexes(self, cursor):
        """Create additional indexes for performance"""
        # Additional indexes are already created in individual table methods
        pass
        
    def _insert_initial_data(self, cursor):
        """Insert initial system data"""
        # Insert default organization
        cursor.execute("""
            INSERT OR IGNORE INTO organizations (name, slug, description, type, is_active) 
            VALUES ('Default Organization', 'default', 'Default organization for system', 'business', 1)
        """)
        
        # Insert default configurations
        configs = [
            ('app_name', 'AI Share Platform', 'string', 'Application name', 'general', 0),
            ('maintenance_mode', 'false', 'boolean', 'Maintenance mode status', 'system', 0),
            ('max_file_size_mb', '100', 'integer', 'Maximum file upload size in MB', 'upload', 0),
            ('allowed_file_types', 'csv,json,xlsx,txt,pdf,docx', 'string', 'Allowed file types for upload', 'upload', 0),
            ('default_ai_model', 'gemini-2.0-flash-exp', 'string', 'Default AI model for chat', 'ai', 0),
        ]
        
        for config in configs:
            cursor.execute("""
                INSERT OR IGNORE INTO configurations (key, value, value_type, description, category, is_sensitive) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, config)