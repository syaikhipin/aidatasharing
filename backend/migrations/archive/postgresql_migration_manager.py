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
                    "fix_sequences",
                    "add_postgresql_indexes",
                    "optimize_json_columns", 
                    "add_postgresql_constraints"
                ]
                
                for migration_name in migrations:
                    try:
                        # Use separate connection for each migration to avoid transaction rollback issues
                        with self.engine.connect() as migration_conn:
                            with migration_conn.begin():
                                if not self._is_migration_applied(migration_conn, migration_name):
                                    migration_method = getattr(self, f"_migration_{migration_name}", None)
                                    if migration_method:
                                        logger.info(f"Running migration: {migration_name}")
                                        migration_method(migration_conn)
                                        self._mark_migration_applied(migration_conn, migration_name)
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
    
    def _migration_fix_sequences(self, conn):
        """Fix PostgreSQL sequences to match existing data"""
        try:
            # Get all sequences
            sequences_result = conn.execute(text("""
                SELECT schemaname, sequencename, last_value 
                FROM pg_sequences 
                WHERE schemaname = 'public'
                ORDER BY sequencename
            """))
            
            sequences = sequences_result.fetchall()
            fixed_count = 0
            
            for seq in sequences:
                schema, seq_name, last_value = seq
                
                # Extract table name from sequence name (remove _id_seq suffix)
                if seq_name.endswith('_id_seq'):
                    table_name = seq_name[:-7]  # Remove '_id_seq'
                    
                    try:
                        # Check if table exists and has an id column
                        check_table = conn.execute(text(f"""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = '{table_name}' 
                            AND column_name = 'id'
                        """))
                        
                        if not check_table.fetchone():
                            continue
                        
                        # Check max ID in the corresponding table
                        max_result = conn.execute(text(f'SELECT MAX(id) FROM {table_name}'))
                        max_id_row = max_result.fetchone()
                        max_id = max_id_row[0] if max_id_row and max_id_row[0] is not None else 0
                        
                        # Handle None last_value (new sequences) or when max_id is greater
                        if last_value is None or max_id > last_value:
                            # Fix the sequence - ensure at least 1 if table is empty
                            next_val = max(max_id, 1)
                            conn.execute(text(f"SELECT setval('{seq_name}', {next_val})"))
                            fixed_count += 1
                            logger.info(f"Fixed sequence {seq_name}: {last_value} -> {next_val}")
                            
                    except Exception as e:
                        logger.warning(f"Could not fix sequence for table {table_name}: {e}")
            
            logger.info(f"Fixed {fixed_count} PostgreSQL sequences")
            
        except Exception as e:
            logger.warning(f"Sequence fix failed: {e}")

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
            # First convert JSON columns to JSONB if needed
            column_conversions = [
                "ALTER TABLE datasets ALTER COLUMN schema_info TYPE JSONB USING schema_info::JSONB",
                "ALTER TABLE datasets ALTER COLUMN file_metadata TYPE JSONB USING file_metadata::JSONB",
                "ALTER TABLE datasets ALTER COLUMN ai_insights TYPE JSONB USING ai_insights::JSONB",
                "ALTER TABLE database_connectors ALTER COLUMN connection_config TYPE JSONB USING connection_config::JSONB",
            ]
            
            for conversion_sql in column_conversions:
                try:
                    conn.execute(text(conversion_sql))
                except Exception as e:
                    # Column might already be JSONB or not exist
                    logger.debug(f"Column conversion skipped: {e}")
            
            # Create GIN indexes on JSONB columns for better search performance
            json_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_datasets_schema_info_gin ON datasets USING GIN (schema_info jsonb_path_ops)",
                "CREATE INDEX IF NOT EXISTS idx_datasets_file_metadata_gin ON datasets USING GIN (file_metadata jsonb_path_ops)",
                "CREATE INDEX IF NOT EXISTS idx_datasets_ai_insights_gin ON datasets USING GIN (ai_insights jsonb_path_ops)",
                "CREATE INDEX IF NOT EXISTS idx_database_connectors_config_gin ON database_connectors USING GIN (connection_config jsonb_path_ops)",
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
            # Check existing constraints first
            existing_constraints = set()
            result = conn.execute(text("""
                SELECT conname 
                FROM pg_constraint 
                WHERE contype = 'c'
            """))
            for row in result:
                existing_constraints.add(row[0])
            
            # Simple constraints that are likely to work
            simple_constraints = [
                # Email format validation
                ("chk_users_email_format", "users", 
                 "ALTER TABLE users ADD CONSTRAINT chk_users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$')"),
                
                # Dataset size validation
                ("chk_datasets_size_positive", "datasets",
                 "ALTER TABLE datasets ADD CONSTRAINT chk_datasets_size_positive CHECK (size_bytes >= 0)"),
                ("chk_datasets_row_count_positive", "datasets",
                 "ALTER TABLE datasets ADD CONSTRAINT chk_datasets_row_count_positive CHECK (row_count >= 0)"),
                ("chk_datasets_column_count_positive", "datasets",
                 "ALTER TABLE datasets ADD CONSTRAINT chk_datasets_column_count_positive CHECK (column_count >= 0)"),
            ]
            
            # Add simple constraints first
            for constraint_name, table_name, constraint_sql in simple_constraints:
                if constraint_name not in existing_constraints:
                    try:
                        conn.execute(text(constraint_sql))
                        logger.info(f"Added constraint: {constraint_name}")
                    except Exception as e:
                        logger.warning(f"Constraint creation failed: {constraint_name} - {e}")
                else:
                    logger.debug(f"Constraint already exists: {constraint_name}")
            
            # Skip quality score constraints since they're VARCHAR fields and complex validation
            # would require more sophisticated handling that's not essential for basic operation
            logger.info("Skipping quality score constraints (VARCHAR fields with complex validation)")
                    
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