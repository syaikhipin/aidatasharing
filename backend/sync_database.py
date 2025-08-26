#!/usr/bin/env python3
"""
Database Synchronization Script
Ensures the backend uses the correct database from storage/aishare_platform.db
"""

import os
import sys
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sync_database():
    """Sync database configuration to use storage/aishare_platform.db"""
    
    # Define paths
    backend_dir = Path(__file__).parent
    root_dir = backend_dir.parent
    storage_db_path = root_dir / "storage" / "aishare_platform.db"
    backend_db_path = backend_dir / "ai_share_platform.db"
    
    logger.info(f"Backend directory: {backend_dir}")
    logger.info(f"Storage database path: {storage_db_path}")
    
    # Check if storage database exists
    if not storage_db_path.exists():
        logger.error(f"Storage database not found at {storage_db_path}")
        return False
    
    # Update .env file to point to the correct database
    env_file_path = backend_dir / ".env"
    if env_file_path.exists():
        logger.info("Updating .env file with correct database path...")
        
        # Read existing .env
        with open(env_file_path, 'r') as f:
            lines = f.readlines()
        
        # Update DATABASE_URL
        updated_lines = []
        database_url_found = False
        
        for line in lines:
            if line.startswith('DATABASE_URL='):
                updated_lines.append(f'DATABASE_URL=sqlite:///../storage/aishare_platform.db\n')
                database_url_found = True
                logger.info("Updated DATABASE_URL in .env")
            else:
                updated_lines.append(line)
        
        # Add DATABASE_URL if not found
        if not database_url_found:
            updated_lines.append(f'\n# Database configuration\n')
            updated_lines.append(f'DATABASE_URL=sqlite:///../storage/aishare_platform.db\n')
            logger.info("Added DATABASE_URL to .env")
        
        # Write updated .env
        with open(env_file_path, 'w') as f:
            f.writelines(updated_lines)
    else:
        logger.warning(".env file not found. Creating one with DATABASE_URL...")
        with open(env_file_path, 'w') as f:
            f.write('# Database configuration\n')
            f.write('DATABASE_URL=sqlite:///../storage/aishare_platform.db\n')
    
    # Remove the empty backend database if it exists
    if backend_db_path.exists() and backend_db_path.stat().st_size == 0:
        logger.info(f"Removing empty database at {backend_db_path}")
        backend_db_path.unlink()
    
    # Create a symlink from backend to storage database (optional)
    # This helps with legacy code that might look for the database in the backend directory
    if not backend_db_path.exists():
        logger.info(f"Creating symlink from {backend_db_path} to {storage_db_path}")
        try:
            backend_db_path.symlink_to(storage_db_path.resolve())
            logger.info("Symlink created successfully")
        except Exception as e:
            logger.warning(f"Could not create symlink: {e}")
            logger.info("Applications will need to use the DATABASE_URL from .env")
    
    # Update config.py to ensure it uses the correct path
    config_file = backend_dir / "app" / "core" / "config.py"
    if config_file.exists():
        logger.info("Checking config.py for correct database configuration...")
        
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Check if DATABASE_URL is properly configured
        if 'DATABASE_URL' in content:
            if '../storage/aishare_platform.db' not in content and 'getenv' in content:
                logger.info("Config.py uses environment variable for DATABASE_URL - good!")
            else:
                logger.warning("Config.py might need manual review for DATABASE_URL configuration")
    
    logger.info("Database synchronization completed successfully!")
    logger.info(f"The backend will now use the database at: {storage_db_path}")
    
    return True

def check_database_status():
    """Check the status of the database"""
    import sqlite3
    
    backend_dir = Path(__file__).parent
    root_dir = backend_dir.parent
    storage_db_path = root_dir / "storage" / "aishare_platform.db"
    
    if not storage_db_path.exists():
        logger.error(f"Database not found at {storage_db_path}")
        return
    
    try:
        conn = sqlite3.connect(str(storage_db_path))
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        logger.info(f"Database at {storage_db_path} contains {len(tables)} tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            logger.info(f"  - {table[0]}: {count} rows")
        
        # Check for shared datasets
        cursor.execute("""
            SELECT COUNT(*) FROM datasets 
            WHERE public_share_enabled = 1 AND share_token IS NOT NULL
        """)
        shared_count = cursor.fetchone()[0]
        logger.info(f"\nShared datasets: {shared_count}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error checking database: {e}")

if __name__ == "__main__":
    logger.info("Starting database synchronization...")
    
    if sync_database():
        logger.info("\n" + "="*50)
        check_database_status()
        logger.info("="*50)
        logger.info("\n✅ Database synchronization successful!")
        logger.info("Please restart the backend server to use the updated configuration.")
    else:
        logger.error("❌ Database synchronization failed!")
        sys.exit(1)