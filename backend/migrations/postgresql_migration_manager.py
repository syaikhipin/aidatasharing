#!/usr/bin/env python3
"""
PostgreSQL Migration Manager
Handles PostgreSQL-specific migrations and database setup.
Created: 2025-08-26
"""

import logging
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import Base

logger = logging.getLogger(__name__)

class PostgreSQLMigrationManager:
    """PostgreSQL-specific migration manager"""
    
    def __init__(self):
        self.database_url = settings.DATABASE_URL
        self.engine = create_engine(
            self.database_url,
            # Use configuration from .env file
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=settings.DB_POOL_PRE_PING,
            pool_recycle=settings.DB_POOL_RECYCLE,
            connect_args={
                "connect_timeout": settings.DB_CONNECTION_TIMEOUT,
            } if "postgresql" in settings.DATABASE_URL else {}
        )
    
    def migrate(self):
        """Run all PostgreSQL migrations"""
        try:
            logger.info("Starting PostgreSQL migrations...")
            
            # Ensure all tables exist
            self._ensure_schema()
            
            # Run specific migrations
            self._run_migrations()
            
            logger.info("PostgreSQL migrations completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL migration failed: {e}")
            return False
    
    def _ensure_schema(self):
        """Ensure all tables exist in the schema"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("PostgreSQL schema ensured")
        except Exception as e:
            logger.error(f"Schema creation failed: {e}")
            raise
    
    def _run_migrations(self):
        """Run PostgreSQL-specific migrations"""
        try:
            # Run each migration in its own transaction to avoid rollback issues
            with self.engine.connect() as conn:
                # Create migration tracking table first
                with conn.begin():
                    self._create_migration_tracking_table(conn)
                
                # List of migrations to run
                migrations = [
                    "add_postgresql_indexes",
                    "optimize_json_columns", 
                    "add_postgresql_constraints"
                ]
                
                for migration_name in migrations:
                    try:
                        with conn.begin():
                            if not self._is_migration_applied(conn, migration_name):
                                migration_method = getattr(self, f"_migration_{migration_name}", None)
                                if migration_method:
                                    logger.info(f"Running migration: {migration_name}")
                                    migration_method(conn)
                                    self._mark_migration_applied(conn, migration_name)
                                else:
                                    logger.warning(f"Migration method not found: {migration_name}")
                    except Exception as e:
                        logger.warning(f"Migration {migration_name} failed: {e}")
                        # Continue with other migrations
                        continue
        
        except Exception as e:
            logger.error(f"Migration execution failed: {e}")
            raise
    
    def _create_migration_tracking_table(self, conn):
        """Create migration tracking table if it doesn't exist"""
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                migration_name VARCHAR(255) UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
    
    def _is_migration_applied(self, conn, migration_name):
        """Check if a migration has been applied"""
        result = conn.execute(
            text("SELECT COUNT(*) FROM schema_migrations WHERE migration_name = :name"),
            {"name": migration_name}
        )
        return result.scalar() > 0
    
    def _mark_migration_applied(self, conn, migration_name):
        """Mark a migration as applied"""
        conn.execute(
            text("INSERT INTO schema_migrations (migration_name) VALUES (:name) ON CONFLICT (migration_name) DO NOTHING"),
            {"name": migration_name}
        )
    
    def _migration_add_postgresql_indexes(self, conn):
        """Add PostgreSQL-specific indexes for better performance"""
        indexes = [
            # Users indexes
            "CREATE INDEX IF NOT EXISTS idx_users_email_active ON users (email, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_users_organization ON users (organization_id)",
            
            # Datasets indexes
            "CREATE INDEX IF NOT EXISTS idx_datasets_owner_active ON datasets (owner_id, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_datasets_type_status ON datasets (type, status)",
            "CREATE INDEX IF NOT EXISTS idx_datasets_organization ON datasets (organization_id)",
            "CREATE INDEX IF NOT EXISTS idx_datasets_created_at ON datasets (created_at DESC)",
            
            # Access logs indexes
            "CREATE INDEX IF NOT EXISTS idx_dataset_access_logs_dataset ON dataset_access_logs (dataset_id, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_dataset_access_logs_user ON dataset_access_logs (user_id, created_at DESC)",
            
            # Downloads indexes
            "CREATE INDEX IF NOT EXISTS idx_dataset_downloads_dataset ON dataset_downloads (dataset_id, created_at DESC)",
            
            # Organizations indexes
            "CREATE INDEX IF NOT EXISTS idx_organizations_active ON organizations (is_active)",
            "CREATE INDEX IF NOT EXISTS idx_organizations_type ON organizations (type)",
        ]
        
        for index_sql in indexes:
            try:
                conn.execute(text(index_sql))
            except Exception as e:
                logger.warning(f"Index creation failed: {index_sql} - {e}")
    
    def _migration_optimize_json_columns(self, conn):
        """Add PostgreSQL-specific optimizations for JSON columns"""
        try:
            # Create GIN indexes on JSON columns for better search performance
            json_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_datasets_schema_info_gin ON datasets USING GIN (schema_info)",
                "CREATE INDEX IF NOT EXISTS idx_datasets_file_metadata_gin ON datasets USING GIN (file_metadata)",
                "CREATE INDEX IF NOT EXISTS idx_datasets_ai_insights_gin ON datasets USING GIN (ai_insights)",
                "CREATE INDEX IF NOT EXISTS idx_database_connectors_config_gin ON database_connectors USING GIN (connection_config)",
            ]
            
            for index_sql in json_indexes:
                try:
                    conn.execute(text(index_sql))
                except Exception as e:
                    logger.warning(f"JSON index creation failed: {index_sql} - {e}")
                    
        except Exception as e:
            logger.warning(f"JSON optimization failed: {e}")
    
    def _migration_add_postgresql_constraints(self, conn):
        """Add PostgreSQL-specific constraints"""
        try:
            constraints = [
                # Email format validation
                "ALTER TABLE users ADD CONSTRAINT IF NOT EXISTS chk_users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$')",
                
                # Dataset size validation
                "ALTER TABLE datasets ADD CONSTRAINT IF NOT EXISTS chk_datasets_size_positive CHECK (size_bytes >= 0)",
                "ALTER TABLE datasets ADD CONSTRAINT IF NOT EXISTS chk_datasets_row_count_positive CHECK (row_count >= 0)",
                "ALTER TABLE datasets ADD CONSTRAINT IF NOT EXISTS chk_datasets_column_count_positive CHECK (column_count >= 0)",
                
                # Quality scores validation
                "ALTER TABLE datasets ADD CONSTRAINT IF NOT EXISTS chk_datasets_quality_score CHECK (data_quality_score >= 0 AND data_quality_score <= 1)",
                "ALTER TABLE datasets ADD CONSTRAINT IF NOT EXISTS chk_datasets_completeness_score CHECK (completeness_score >= 0 AND completeness_score <= 1)",
                "ALTER TABLE datasets ADD CONSTRAINT IF NOT EXISTS chk_datasets_consistency_score CHECK (consistency_score >= 0 AND consistency_score <= 1)",
                "ALTER TABLE datasets ADD CONSTRAINT IF NOT EXISTS chk_datasets_accuracy_score CHECK (accuracy_score >= 0 AND accuracy_score <= 1)",
            ]
            
            for constraint_sql in constraints:
                try:
                    conn.execute(text(constraint_sql))
                except Exception as e:
                    logger.warning(f"Constraint creation failed: {constraint_sql} - {e}")
                    
        except Exception as e:
            logger.warning(f"Constraint creation failed: {e}")

def main():
    """Main function for testing the migration manager"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    migration_manager = PostgreSQLMigrationManager()
    success = migration_manager.migrate()
    
    if success:
        print("✅ PostgreSQL migrations completed successfully!")
    else:
        print("❌ PostgreSQL migrations failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()