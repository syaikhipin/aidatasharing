"""
Migration script to add connector_id relationship to datasets table
"""

import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def migrate_add_connector_dataset_relationship():
    """Add connector_id foreign key to datasets table"""
    
    # Database path
    db_path = Path(__file__).parent.parent.parent / "app.db"
    
    if not db_path.exists():
        logger.info("Database doesn't exist yet, skipping migration")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if connector_id column already exists
        cursor.execute("PRAGMA table_info(datasets)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'connector_id' not in columns:
            logger.info("Adding connector_id column to datasets table...")
            
            # Add the connector_id column
            cursor.execute("""
                ALTER TABLE datasets 
                ADD COLUMN connector_id INTEGER 
                REFERENCES database_connectors(id)
            """)
            
            # Create index for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_datasets_connector_id 
                ON datasets(connector_id)
            """)
            
            conn.commit()
            logger.info("Successfully added connector_id relationship to datasets table")
        else:
            logger.info("connector_id column already exists in datasets table")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_add_connector_dataset_relationship() 