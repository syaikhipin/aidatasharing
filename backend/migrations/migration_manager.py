#!/usr/bin/env python3
"""
Database Migration Manager
Handles database schema changes and migrations in a systematic way.
Integrates with the consolidated migration system.
"""

import os
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
import importlib.util

logger = logging.getLogger(__name__)

class MigrationManager:
    """Manages database migrations with consolidated migration support"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Extract from DATABASE_URL environment variable or use default
            try:
                from app.core.config import settings
                db_path = settings.DATABASE_URL.replace('sqlite:///', '')
            except (ImportError, AttributeError):
                # Fallback to default path
                db_path = str(Path("../storage/aishare_platform.db").resolve())
        
        self.db_path = db_path
        self.migrations_dir = Path(__file__).parent / "versions"
        self.migrations_dir.mkdir(exist_ok=True)
        self.consolidated_migration_path = Path(__file__).parent / "consolidated_migration.py"
        
    def _ensure_migrations_table(self, cursor):
        """Ensure the migrations tracking table exists"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version VARCHAR(255) UNIQUE NOT NULL,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                checksum VARCHAR(255),
                migration_type VARCHAR(50) DEFAULT 'individual'
            )
        """)
    
    def _get_applied_migrations(self, cursor) -> List[str]:
        """Get list of already applied migrations"""
        cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
        return [row[0] for row in cursor.fetchall()]
    
    def _check_consolidated_migration_applied(self, cursor) -> bool:
        """Check if consolidated migration has been applied"""
        cursor.execute(
            "SELECT COUNT(*) FROM schema_migrations WHERE version = 'consolidated_v1' AND migration_type = 'consolidated'"
        )
        return cursor.fetchone()[0] > 0
    
    def _get_pending_migrations(self) -> List[Dict[str, Any]]:
        """Get list of pending migrations"""
        migration_files = []
        
        # Scan migrations directory for .py files
        for file_path in sorted(self.migrations_dir.glob("*.py")):
            if file_path.name.startswith("__"):
                continue
                
            version = file_path.stem
            migration_files.append({
                "version": version,
                "file_path": file_path,
                "description": self._extract_description(file_path)
            })
        
        return migration_files
    
    def _extract_description(self, file_path: Path) -> str:
        """Extract description from migration file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                # Look for description in docstring or comment
                lines = content.split('\n')
                for line in lines[:10]:  # Check first 10 lines
                    if 'description' in line.lower() or '"""' in line:
                        return line.strip().replace('"""', '').replace('#', '').strip()
                return "No description"
        except Exception:
            return "No description"
    
    def _run_consolidated_migration(self, cursor) -> bool:
        """Run the consolidated migration"""
        try:
            logger.info("Running consolidated migration...")
            
            # Import the consolidated migration module
            spec = importlib.util.spec_from_file_location(
                "consolidated_migration", 
                self.consolidated_migration_path
            )
            consolidated_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(consolidated_module)
            
            # Create an instance and run the migration
            migration_instance = consolidated_module.ConsolidatedMigration(
                database_url=f"sqlite:///{self.db_path}"
            )
            
            # Execute the migration (but we need to handle this differently since it creates its own connection)
            # We'll use the existing cursor instead
            migration_instance.database_path = Path(self.db_path)
            
            # Call individual table creation methods
            migration_instance._create_users_table(cursor)
            migration_instance._create_organizations_table(cursor)
            migration_instance._create_datasets_table(cursor)
            migration_instance._create_models_table(cursor)
            migration_instance._create_file_uploads_table(cursor)
            migration_instance._create_data_connectors_table(cursor)
            migration_instance._create_proxy_connectors_table(cursor)
            migration_instance._create_shared_proxy_links_table(cursor)
            migration_instance._create_shared_datasets_table(cursor)
            migration_instance._create_chat_sessions_table(cursor)
            migration_instance._create_chat_messages_table(cursor)
            migration_instance._create_access_requests_table(cursor)
            migration_instance._create_notifications_table(cursor)
            migration_instance._create_audit_logs_table(cursor)
            migration_instance._create_analytics_table(cursor)
            migration_instance._create_admin_config_table(cursor)
            migration_instance._create_indexes(cursor)
            migration_instance._insert_initial_data(cursor)
            
            # Record the consolidated migration as applied
            cursor.execute(
                "INSERT INTO schema_migrations (version, description, migration_type) VALUES (?, ?, ?)",
                ("consolidated_v1", "Consolidated database migration - all tables and initial data", "consolidated")
            )
            
            logger.info("Consolidated migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Consolidated migration failed: {e}")
            return False
    
    def _execute_migration(self, cursor, migration_info: Dict[str, Any]):
        """Execute a single migration"""
        version = migration_info["version"]
        file_path = migration_info["file_path"]
        
        logger.info(f"Applying migration {version}...")
        
        try:
            # Import and execute the migration
            spec = importlib.util.spec_from_file_location(version, file_path)
            migration_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(migration_module)
            
            if hasattr(migration_module, 'upgrade'):
                migration_module.upgrade(cursor)
            else:
                logger.warning(f"Migration {version} has no upgrade function")
            
            # Record the migration as applied
            cursor.execute(
                "INSERT INTO schema_migrations (version, description, migration_type) VALUES (?, ?, ?)",
                (version, migration_info["description"], "individual")
            )
            
            logger.info(f"Migration {version} applied successfully")
            
        except Exception as e:
            logger.error(f"Failed to apply migration {version}: {e}")
            raise
    
    def migrate(self) -> Dict[str, Any]:
        """Run all pending migrations"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Ensure migrations table exists
            self._ensure_migrations_table(cursor)
            
            # Check if database is empty (no tables except migrations table)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'schema_migrations'")
            existing_tables = cursor.fetchall()
            
            executed = []
            
            # If database is empty or has very few tables, run consolidated migration
            if len(existing_tables) < 5 and not self._check_consolidated_migration_applied(cursor):
                logger.info("Database appears to be new or incomplete. Running consolidated migration...")
                if self._run_consolidated_migration(cursor):
                    executed.append("consolidated_v1")
                else:
                    conn.rollback()
                    conn.close()
                    return {
                        "status": "error",
                        "message": "Consolidated migration failed",
                        "executed": []
                    }
            
            # Get applied and pending migrations
            applied = self._get_applied_migrations(cursor)
            all_migrations = self._get_pending_migrations()
            
            # Filter out already applied migrations
            pending = [m for m in all_migrations if m["version"] not in applied]
            
            if not pending:
                if not executed:
                    logger.info("No pending migrations")
                conn.commit()
                conn.close()
                return {
                    "status": "success",
                    "message": "No pending migrations" if not executed else f"Applied {len(executed)} migrations",
                    "executed": executed
                }
            
            # Apply pending individual migrations
            for migration in pending:
                try:
                    self._execute_migration(cursor, migration)
                    executed.append(migration["version"])
                except Exception as e:
                    logger.error(f"Failed to apply migration {migration['version']}: {e}")
                    conn.rollback()
                    conn.close()
                    return {
                        "status": "error",
                        "message": f"Migration {migration['version']} failed: {e}",
                        "executed": executed
                    }
            
            conn.commit()
            conn.close()
            
            return {
                "status": "success",
                "message": f"Applied {len(executed)} migrations",
                "executed": executed
            }
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            if 'conn' in locals():
                try:
                    conn.rollback()
                    conn.close()
                except:
                    pass
            return {
                "status": "error",
                "message": str(e),
                "executed": []
            }
    
    def create_migration(self, name: str, description: str = "") -> str:
        """Create a new migration file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version = f"{timestamp}_{name}"
        file_path = self.migrations_dir / f"{version}.py"
        
        template = f'''#!/usr/bin/env python3
"""
Migration: {description or name}
Created: {datetime.now().isoformat()}
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)

def upgrade(cursor):
    """Apply the migration"""
    # Add your migration code here
    # Example:
    # cursor.execute("""
    #     ALTER TABLE some_table ADD COLUMN new_column VARCHAR(255)
    # """)
    pass

def downgrade(cursor):
    """Rollback the migration (optional)"""
    # Add rollback code here if needed
    # Example:
    # cursor.execute("""
    #     ALTER TABLE some_table DROP COLUMN new_column
    # """)
    pass
'''
        
        with open(file_path, 'w') as f:
            f.write(template)
        
        logger.info(f"Created migration file: {file_path}")
        return str(file_path)
    
    def status(self) -> Dict[str, Any]:
        """Get migration status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            self._ensure_migrations_table(cursor)
            
            # Get applied migrations with details
            cursor.execute("""
                SELECT version, description, migration_type, applied_at 
                FROM schema_migrations 
                ORDER BY applied_at
            """)
            applied_details = cursor.fetchall()
            
            all_migrations = self._get_pending_migrations()
            applied_versions = [row[0] for row in applied_details]
            pending = [m for m in all_migrations if m["version"] not in applied_versions]
            
            # Check if consolidated migration was applied
            consolidated_applied = self._check_consolidated_migration_applied(cursor)
            
            conn.close()
            
            return {
                "consolidated_applied": consolidated_applied,
                "applied_count": len(applied_details),
                "pending_count": len(pending),
                "applied": [
                    {
                        "version": row[0],
                        "description": row[1],
                        "type": row[2],
                        "applied_at": row[3]
                    } for row in applied_details
                ],
                "pending": [
                    {
                        "version": m["version"],
                        "description": m["description"]
                    } for m in pending
                ]
            }
            
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def reset_database(self) -> Dict[str, Any]:
        """Reset database by dropping all tables and re-running consolidated migration"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            # Drop all tables
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
            
            # Re-run consolidated migration
            self._ensure_migrations_table(cursor)
            if self._run_consolidated_migration(cursor):
                conn.commit()
                conn.close()
                return {
                    "status": "success",
                    "message": "Database reset and consolidated migration applied successfully"
                }
            else:
                conn.rollback()
                conn.close()
                return {
                    "status": "error",
                    "message": "Failed to apply consolidated migration after reset"
                }
                
        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            if 'conn' in locals():
                try:
                    conn.rollback()
                    conn.close()
                except:
                    pass
            return {
                "status": "error",
                "message": str(e)
            }

if __name__ == "__main__":
    # CLI interface for migrations
    import sys
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    manager = MigrationManager()
    
    if len(sys.argv) < 2:
        print("Usage: python migration_manager.py [migrate|status|create <name>|reset]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "migrate":
        result = manager.migrate()
        print(f"Migration result: {result}")
    elif command == "status":
        status = manager.status()
        print(f"Migration status: {status}")
    elif command == "create" and len(sys.argv) > 2:
        name = sys.argv[2]
        description = sys.argv[3] if len(sys.argv) > 3 else ""
        file_path = manager.create_migration(name, description)
        print(f"Created migration: {file_path}")
    elif command == "reset":
        result = manager.reset_database()
        print(f"Reset result: {result}")
    else:
        print("Invalid command. Available commands: migrate, status, create <name>, reset")
        sys.exit(1)