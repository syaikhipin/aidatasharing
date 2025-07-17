#!/usr/bin/env python3
"""
Fresh Installation Migration Script
Consolidates all databases and creates clean schema for new installations
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import Base
from app.models.user import User
from app.models.organization import Organization, Department
from app.models.dataset import Dataset, DatabaseConnector, DatasetType, DatasetStatus
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FreshInstallMigration:
    """Handles fresh installation database setup"""
    
    def __init__(self):
        self.db_path = "./storage/aishare_platform.db"
        self.backup_path = f"./storage/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def run_migration(self):
        """Run the complete fresh installation migration"""
        logger.info("🚀 Starting Fresh Installation Migration...")
        
        try:
            # Step 1: Backup existing databases
            self.backup_existing_databases()
            
            # Step 2: Create unified database
            self.create_unified_database()
            
            # Step 3: Create all tables
            self.create_database_schema()
            
            # Step 4: Insert default data
            self.insert_default_data()
            
            # Step 5: Clean up old databases
            self.cleanup_old_databases()
            
            # Step 6: Update configuration files
            self.update_configuration()
            
            logger.info("✅ Fresh Installation Migration completed successfully!")
            logger.info(f"📁 New database location: {self.db_path}")
            logger.info(f"💾 Backups stored in: {self.backup_path}")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise
    
    def backup_existing_databases(self):
        """Backup existing database files"""
        logger.info("📦 Backing up existing databases...")
        
        os.makedirs(self.backup_path, exist_ok=True)
        
        db_files = [
            "./app.db",
            "./backend/app.db", 
            "./backend/storage/mindsdb.sqlite3.db",
            "./storage/tasks.db",
            "./storage/mindsdb.db"
        ]
        
        for db_file in db_files:
            if os.path.exists(db_file):
                backup_name = f"{Path(db_file).name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                backup_path = os.path.join(self.backup_path, backup_name)
                
                try:
                    import shutil
                    shutil.copy2(db_file, backup_path)
                    logger.info(f"   ✅ Backed up: {db_file} -> {backup_path}")
                except Exception as e:
                    logger.warning(f"   ⚠️  Failed to backup {db_file}: {e}")
    
    def create_unified_database(self):
        """Create the unified database"""
        logger.info("🗄️  Creating unified database...")
        
        # Ensure storage directory exists
        os.makedirs("./storage", exist_ok=True)
        
        # Create database connection
        database_url = f"sqlite:///{self.db_path}"
        self.engine = create_engine(database_url, echo=False)
        
        logger.info(f"   ✅ Database created: {self.db_path}")
    
    def create_database_schema(self):
        """Create all database tables"""
        logger.info("📋 Creating database schema...")
        
        # Create all tables
        Base.metadata.create_all(bind=self.engine)
        
        # Add document support fields manually (since they might not be in the models yet)
        with self.engine.connect() as connection:
            try:
                # Check if columns exist before adding them
                result = connection.execute(text("PRAGMA table_info(datasets)"))
                existing_columns = [row[1] for row in result.fetchall()]
                
                document_columns = [
                    ("document_type", "VARCHAR"),
                    ("page_count", "INTEGER"),
                    ("word_count", "INTEGER"), 
                    ("extracted_text", "TEXT"),
                    ("text_extraction_method", "VARCHAR")
                ]
                
                for col_name, col_type in document_columns:
                    if col_name not in existing_columns:
                        connection.execute(text(f"ALTER TABLE datasets ADD COLUMN {col_name} {col_type}"))
                        logger.info(f"   ✅ Added column: {col_name}")
                
                connection.commit()
                
            except Exception as e:
                logger.warning(f"   ⚠️  Error adding document columns: {e}")
        
        logger.info("   ✅ Database schema created successfully")
    
    def insert_default_data(self):
        """Insert default organizations and admin user"""
        logger.info("👤 Creating default data...")
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        db = SessionLocal()
        
        try:
            # Create default organization
            default_org = Organization(
                name="Default Organization",
                slug="default-org",
                description="Default organization for AI Share Platform",
                is_active=True,
                allow_external_sharing=True
            )
            db.add(default_org)
            db.commit()
            db.refresh(default_org)
            
            # Create admin user
            from app.core.auth import get_password_hash
            
            admin_user = User(
                email="admin@aishare.com",
                full_name="System Administrator",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_superuser=True,
                organization_id=default_org.id
            )
            db.add(admin_user)
            db.commit()
            
            logger.info("   ✅ Default organization created")
            logger.info("   ✅ Admin user created (admin@aishare.com / admin123)")
            
        except Exception as e:
            logger.error(f"   ❌ Failed to create default data: {e}")
            db.rollback()
        finally:
            db.close()
    
    def cleanup_old_databases(self):
        """Remove old database files"""
        logger.info("🧹 Cleaning up old database files...")
        
        old_db_files = [
            "./app.db",
            "./backend/app.db"
        ]
        
        for db_file in old_db_files:
            if os.path.exists(db_file):
                try:
                    os.remove(db_file)
                    logger.info(f"   ✅ Removed: {db_file}")
                except Exception as e:
                    logger.warning(f"   ⚠️  Failed to remove {db_file}: {e}")
    
    def update_configuration(self):
        """Update configuration files with unified database path"""
        logger.info("⚙️  Updating configuration files...")
        
        # Update main .env file
        self.update_env_file(".env")
        
        # Update backend .env file
        self.update_env_file("backend/.env")
        
        # Update database configuration in backend
        self.update_database_config()
        
        logger.info("   ✅ Configuration files updated")
    
    def update_env_file(self, env_path):
        """Update environment file with unified database path"""
        if not os.path.exists(env_path):
            return
            
        try:
            with open(env_path, 'r') as f:
                content = f.read()
            
            # Update database URL
            lines = content.split('\n')
            updated_lines = []
            
            for line in lines:
                if line.startswith('DATABASE_URL='):
                    updated_lines.append(f'DATABASE_URL=sqlite:///./storage/aishare_platform.db')
                else:
                    updated_lines.append(line)
            
            with open(env_path, 'w') as f:
                f.write('\n'.join(updated_lines))
                
            logger.info(f"   ✅ Updated: {env_path}")
            
        except Exception as e:
            logger.warning(f"   ⚠️  Failed to update {env_path}: {e}")
    
    def update_database_config(self):
        """Update backend database configuration"""
        config_path = "backend/app/core/database.py"
        
        if not os.path.exists(config_path):
            return
            
        try:
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Update SQLALCHEMY_DATABASE_URL
            if 'SQLALCHEMY_DATABASE_URL = ' in content:
                content = content.replace(
                    'SQLALCHEMY_DATABASE_URL = ',
                    'SQLALCHEMY_DATABASE_URL = "sqlite:///./storage/aishare_platform.db"  # '
                )
                
                with open(config_path, 'w') as f:
                    f.write(content)
                    
                logger.info(f"   ✅ Updated database config: {config_path}")
                
        except Exception as e:
            logger.warning(f"   ⚠️  Failed to update database config: {e}")


def main():
    """Main migration function"""
    migration = FreshInstallMigration()
    migration.run_migration()


if __name__ == "__main__":
    main()