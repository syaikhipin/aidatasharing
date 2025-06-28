"""
Database migration to fix model_name field conflicts with Pydantic
This script renames model_name fields to ai_model_name to avoid Pydantic warnings
"""

import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def migrate_database():
    """Migrate the database to rename model_name fields"""
    
    # Database path
    db_path = "app.db"
    backup_path = f"app.db.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if not os.path.exists(db_path):
        logger.info("Database file not found, skipping migration")
        return
    
    try:
        # Create backup
        logger.info(f"Creating backup: {backup_path}")
        import shutil
        shutil.copy2(db_path, backup_path)
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns exist before renaming
        cursor.execute("PRAGMA table_info(dataset_chat_sessions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'model_name' in columns and 'ai_model_name' not in columns:
            logger.info("Migrating dataset_chat_sessions.model_name to ai_model_name")
            
            # Rename column in dataset_chat_sessions
            cursor.execute("""
                ALTER TABLE dataset_chat_sessions 
                RENAME COLUMN model_name TO ai_model_name
            """)
            
        # Check chat_messages table
        cursor.execute("PRAGMA table_info(chat_messages)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'model_version' in columns and 'ai_model_version' not in columns:
            logger.info("Migrating chat_messages.model_version to ai_model_version")
            
            # Rename column in chat_messages
            cursor.execute("""
                ALTER TABLE chat_messages 
                RENAME COLUMN model_version TO ai_model_version
            """)
        
        # Check dataset_models table
        cursor.execute("PRAGMA table_info(dataset_models)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'model_version' in columns and 'ai_model_version' not in columns:
            logger.info("Migrating dataset_models.model_version to ai_model_version")
            
            # Rename column in dataset_models
            cursor.execute("""
                ALTER TABLE dataset_models 
                RENAME COLUMN model_version TO ai_model_version
            """)
        
        # Commit changes
        conn.commit()
        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        # Restore backup if migration fails
        if os.path.exists(backup_path):
            logger.info("Restoring backup due to migration failure")
            shutil.copy2(backup_path, db_path)
        raise
    
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_database() 