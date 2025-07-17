#!/usr/bin/env python3
"""
Database Migration Manager
Handles database schema changes and migrations in a systematic way.
"""

import os
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Extract from DATABASE_URL environment variable
            from app.core.config import settings
            db_path = settings.DATABASE_URL.replace('sqlite:///', '')
        
        self.db_path = db_path
        self.migrations_dir = Path(__file__).parent / "versions"
        self.migrations_dir.mkdir(exist_ok=True)
        
    def _ensure_migrations_table(self, cursor):
        """Ensure the migrations tracking table exists"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version VARCHAR(255) UNIQUE NOT NULL,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                checksum VARCHAR(255)
            )
        """)
    
    def _get_applied_migrations(self, cursor) -> List[str]:
        """Get list of already applied migrations"""
        cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
        return [row[0] for row in cursor.fetchall()]
    
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
    
    def _execute_migration(self, cursor, migration_info: Dict[str, Any]):
        """Execute a single migration"""
        version = migration_info["version"]
        file_path = migration_info["file_path"]
        
        logger.info(f"Applying migration {version}...")
        
        # Import and execute the migration
        spec = __import__(f"migrations.versions.{version}", fromlist=["upgrade"])
        
        if hasattr(spec, 'upgrade'):
            spec.upgrade(cursor)
        else:
            logger.warning(f"Migration {version} has no upgrade function")
        
        # Record the migration as applied
        cursor.execute(
            "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
            (version, migration_info["description"])
        )
        
        logger.info(f"Migration {version} applied successfully")
    
    def migrate(self) -> Dict[str, Any]:
        """Run all pending migrations"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ensure migrations table exists
            self._ensure_migrations_table(cursor)
            
            # Get applied and pending migrations
            applied = self._get_applied_migrations(cursor)
            all_migrations = self._get_pending_migrations()
            
            # Filter out already applied migrations
            pending = [m for m in all_migrations if m["version"] not in applied]
            
            if not pending:
                logger.info("No pending migrations")
                return {
                    "status": "success",
                    "message": "No pending migrations",
                    "executed": []
                }
            
            executed = []
            for migration in pending:
                try:
                    self._execute_migration(cursor, migration)
                    executed.append(migration["version"])
                except Exception as e:
                    logger.error(f"Failed to apply migration {migration['version']}: {e}")
                    conn.rollback()
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
    pass

def downgrade(cursor):
    """Rollback the migration (optional)"""
    # Add rollback code here if needed
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
            applied = self._get_applied_migrations(cursor)
            all_migrations = self._get_pending_migrations()
            pending = [m for m in all_migrations if m["version"] not in applied]
            
            conn.close()
            
            return {
                "applied_count": len(applied),
                "pending_count": len(pending),
                "applied": applied,
                "pending": [m["version"] for m in pending]
            }
            
        except Exception as e:
            return {
                "error": str(e)
            }

if __name__ == "__main__":
    # CLI interface for migrations
    import sys
    
    manager = MigrationManager()
    
    if len(sys.argv) < 2:
        print("Usage: python migration_manager.py [migrate|status|create <name>]")
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
    else:
        print("Invalid command")
        sys.exit(1)