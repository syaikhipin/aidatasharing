#!/usr/bin/env python3
"""
Current Schema Migration for PostgreSQL
This migration creates all tables to match the current production schema state.
Updated: 2025-01-09
"""

import logging
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)

class CurrentSchemaMigration:
    """Migration that creates all tables matching current production schema"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        
    def create_enums(self, cur):
        """Create custom enum types"""
        enums = [
            ("organizationtype", ["small_business", "medium_business", "large_business", "enterprise", "nonprofit", "education", "government", "startup"]),
            ("datasharinglevel", ["private", "department", "organization", "public"]),
            ("datasettype", ["csv", "json", "excel", "database", "api", "file"]),
            ("datasetstatus", ["active", "inactive", "processing", "error", "archived"]),
            ("activitytype", ["login", "logout", "dataset_create", "dataset_update", "dataset_delete", "dataset_share", "dataset_download", "file_upload"]),
            ("requesttype", ["access", "share", "download", "export"]),
            ("urgency", ["low", "medium", "high", "critical"]),
            ("category", ["business", "analytics", "research", "compliance"]),
            ("metrictype", ["storage", "bandwidth", "requests", "users", "datasets"])
        ]
        
        for enum_name, enum_values in enums:
            try:
                values_str = "', '".join(enum_values)
                cur.execute(f"CREATE TYPE {enum_name} AS ENUM ('{values_str}')")
                print(f"  ✅ Created enum: {enum_name}")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"  ⚠️  Enum {enum_name} already exists")
                else:
                    print(f"  ❌ Error creating enum {enum_name}: {e}")

    def create_core_tables(self, cur):
        """Create core application tables"""
        
        # Organizations table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL UNIQUE,
                slug VARCHAR NOT NULL UNIQUE,
                description TEXT,
                type organizationtype DEFAULT 'small_business',
                is_active BOOLEAN DEFAULT TRUE,
                allow_external_sharing BOOLEAN DEFAULT FALSE,
                default_sharing_level datasharinglevel DEFAULT 'private',
                website VARCHAR,
                contact_email VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR NOT NULL UNIQUE,
                hashed_password VARCHAR NOT NULL,
                full_name VARCHAR,
                is_active BOOLEAN DEFAULT TRUE,
                is_superuser BOOLEAN DEFAULT FALSE,
                organization_id INTEGER REFERENCES organizations(id),
                role VARCHAR DEFAULT 'member',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Datasets table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                description TEXT,
                type datasettype NOT NULL,
                status datasetstatus DEFAULT 'active',
                is_active BOOLEAN DEFAULT TRUE,
                is_deleted BOOLEAN DEFAULT FALSE,
                deleted_at TIMESTAMP,
                deleted_by INTEGER REFERENCES users(id),
                source_url VARCHAR,
                connection_params JSONB,
                connector_id INTEGER,
                is_multi_file_dataset BOOLEAN DEFAULT FALSE,
                primary_file_path VARCHAR,
                owner_id INTEGER NOT NULL REFERENCES users(id),
                organization_id INTEGER NOT NULL REFERENCES organizations(id),
                sharing_level datasharinglevel DEFAULT 'private',
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
        """)
        
        print("  ✅ Created core tables")

    def create_analytics_tables(self, cur):
        """Create analytics and metrics tables"""
        
        tables = [
            # Usage Metrics
            """
            CREATE TABLE IF NOT EXISTS usage_metrics (
                id SERIAL PRIMARY KEY,
                organization_id INTEGER REFERENCES organizations(id),
                user_id INTEGER REFERENCES users(id),
                metric_type metrictype NOT NULL,
                value DOUBLE PRECISION NOT NULL,
                unit VARCHAR,
                period_start TIMESTAMP,
                period_end TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Activity Logs
            """
            CREATE TABLE IF NOT EXISTS activity_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                organization_id INTEGER REFERENCES organizations(id),
                activity_type activitytype NOT NULL,
                resource_id INTEGER,
                resource_type VARCHAR,
                description TEXT,
                meta_data JSON,
                ip_address VARCHAR,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # API Usage
            """
            CREATE TABLE IF NOT EXISTS api_usage (
                id SERIAL PRIMARY KEY,
                request_id VARCHAR,
                endpoint VARCHAR,
                method VARCHAR,
                user_id INTEGER REFERENCES users(id),
                ip_address VARCHAR,
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_status INTEGER,
                response_time_ms INTEGER,
                request_size_bytes INTEGER,
                response_size_bytes INTEGER
            )
            """,
            
            # Usage Stats
            """
            CREATE TABLE IF NOT EXISTS usage_stats (
                id SERIAL PRIMARY KEY,
                date TIMESTAMP,
                period_type VARCHAR,
                dataset_id INTEGER REFERENCES datasets(id),
                user_id INTEGER REFERENCES users(id),
                organization_id INTEGER REFERENCES organizations(id),
                total_views INTEGER DEFAULT 0,
                total_downloads INTEGER DEFAULT 0,
                total_chats INTEGER DEFAULT 0,
                total_api_calls INTEGER DEFAULT 0,
                unique_users INTEGER DEFAULT 0
            )
            """
        ]
        
        for table_sql in tables:
            cur.execute(table_sql)
        
        print("  ✅ Created analytics tables")

    def create_chat_ai_tables(self, cur):
        """Create chat and AI-related tables"""
        
        tables = [
            # Chat Interactions
            """
            CREATE TABLE IF NOT EXISTS chat_interactions (
                id SERIAL PRIMARY KEY,
                interaction_id VARCHAR,
                dataset_id INTEGER REFERENCES datasets(id),
                user_id INTEGER REFERENCES users(id),
                session_id VARCHAR,
                user_message TEXT,
                ai_response TEXT,
                llm_provider VARCHAR,
                llm_model VARCHAR,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                response_time_ms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Chat Sessions
            """
            CREATE TABLE IF NOT EXISTS dataset_chat_sessions (
                id SERIAL PRIMARY KEY,
                dataset_id INTEGER REFERENCES datasets(id),
                user_id INTEGER REFERENCES users(id),
                session_token VARCHAR,
                share_token VARCHAR,
                ip_address VARCHAR,
                user_agent VARCHAR,
                ai_model_name VARCHAR,
                total_messages INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # LLM Configurations
            """
            CREATE TABLE IF NOT EXISTS llm_configurations (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                provider VARCHAR NOT NULL,
                llm_model_name VARCHAR NOT NULL,
                organization_id INTEGER REFERENCES organizations(id),
                api_key VARCHAR,
                api_base VARCHAR,
                model_params JSON,
                litellm_params JSON,
                is_active BOOLEAN DEFAULT TRUE,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        for table_sql in tables:
            cur.execute(table_sql)
        
        print("  ✅ Created chat/AI tables")

    def create_system_tables(self, cur):
        """Create system and configuration tables"""
        
        tables = [
            # Configurations
            """
            CREATE TABLE IF NOT EXISTS configurations (
                id SERIAL PRIMARY KEY,
                key VARCHAR NOT NULL UNIQUE,
                value TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # System Metrics
            """
            CREATE TABLE IF NOT EXISTS system_metrics (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cpu_usage_percent DOUBLE PRECISION,
                memory_usage_percent DOUBLE PRECISION,
                disk_usage_percent DOUBLE PRECISION,
                active_connections INTEGER,
                total_datasets INTEGER,
                total_users INTEGER,
                total_organizations INTEGER
            )
            """,
            
            # Audit Logs
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                action VARCHAR NOT NULL,
                user_id INTEGER REFERENCES users(id),
                dataset_id INTEGER REFERENCES datasets(id),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                ip_address VARCHAR,
                user_agent VARCHAR
            )
            """
        ]
        
        for table_sql in tables:
            cur.execute(table_sql)
        
        print("  ✅ Created system tables")

    def create_indexes(self, cur):
        """Create essential indexes"""
        
        indexes = [
            # Core indexes
            "CREATE INDEX IF NOT EXISTS ix_users_organization_id ON users (organization_id)",
            "CREATE INDEX IF NOT EXISTS ix_datasets_owner_id ON datasets (owner_id)",
            "CREATE INDEX IF NOT EXISTS ix_datasets_organization_id ON datasets (organization_id)",
            "CREATE INDEX IF NOT EXISTS ix_datasets_sharing_level ON datasets (sharing_level)",
            "CREATE INDEX IF NOT EXISTS ix_datasets_is_active ON datasets (is_active)",
            
            # Analytics indexes
            "CREATE INDEX IF NOT EXISTS ix_activity_logs_user_id ON activity_logs (user_id)",
            "CREATE INDEX IF NOT EXISTS ix_activity_logs_created_at ON activity_logs (created_at)",
            "CREATE INDEX IF NOT EXISTS ix_api_usage_user_id ON api_usage (user_id)",
            "CREATE INDEX IF NOT EXISTS ix_api_usage_timestamp ON api_usage (timestamp)",
            
            # Chat indexes
            "CREATE INDEX IF NOT EXISTS ix_chat_interactions_dataset_id ON chat_interactions (dataset_id)",
            "CREATE INDEX IF NOT EXISTS ix_chat_interactions_user_id ON chat_interactions (user_id)",
            "CREATE INDEX IF NOT EXISTS ix_chat_sessions_dataset_id ON dataset_chat_sessions (dataset_id)",
        ]
        
        for index_sql in indexes:
            try:
                cur.execute(index_sql)
            except Exception as e:
                print(f"  ⚠️  Index creation warning: {e}")
        
        print("  ✅ Created indexes")

    def enable_rls_and_policies(self, cur):
        """Enable Row Level Security on all tables"""
        
        # Get all public tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        
        tables = [row[0] for row in cur.fetchall()]
        
        for table in tables:
            try:
                # Enable RLS
                cur.execute(f'ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY')
                
                # Create basic policy - can be customized later
                cur.execute(f'CREATE POLICY IF NOT EXISTS default_policy ON public.{table} FOR ALL USING (false)')
                
            except Exception as e:
                print(f"  ⚠️  RLS warning for {table}: {e}")
        
        print(f"  🔒 Enabled RLS on {len(tables)} tables")

    def run_migration(self):
        """Run the full migration"""
        try:
            conn = psycopg2.connect(self.database_url)
            conn.autocommit = True
            cur = conn.cursor()
            
            print("🚀 Starting Current Schema Migration...")
            
            print("📊 Creating enums...")
            self.create_enums(cur)
            
            print("🏗️  Creating core tables...")
            self.create_core_tables(cur)
            
            print("📈 Creating analytics tables...")
            self.create_analytics_tables(cur)
            
            print("🤖 Creating chat/AI tables...")
            self.create_chat_ai_tables(cur)
            
            print("⚙️  Creating system tables...")
            self.create_system_tables(cur)
            
            print("🔍 Creating indexes...")
            self.create_indexes(cur)
            
            print("🔒 Enabling RLS...")
            self.enable_rls_and_policies(cur)
            
            # Mark migration as applied
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    migration_name VARCHAR NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                INSERT INTO schema_migrations (migration_name) 
                VALUES ('current_schema_migration_v1')
                ON CONFLICT DO NOTHING
            """)
            
            cur.close()
            conn.close()
            
            print("\n✅ Current Schema Migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            return False

if __name__ == "__main__":
    load_dotenv()
    
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
    
    migration = CurrentSchemaMigration(database_url)
    success = migration.run_migration()
    
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
        exit(1)