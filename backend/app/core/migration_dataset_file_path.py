"""
Migration script to add file_path and other missing columns to the datasets table
"""

import logging
import sys
import os
from sqlalchemy import Column, String, JSON, Integer, DateTime
from sqlalchemy.sql import text

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.core.database import engine, Base, SessionLocal
from app.models.dataset import Dataset

logger = logging.getLogger(__name__)

def run_migration():
    """
    Add file_path and other missing columns to the datasets table
    """
    logger.info("Starting migration to add file_path and other columns to datasets table")
    
    # Create a session
    db = SessionLocal()
    
    try:
        # Check if the column exists
        try:
            db.execute(text("SELECT file_path FROM datasets LIMIT 1"))
            logger.info("Column file_path already exists in datasets table")
            file_path_exists = True
        except Exception:
            logger.info("Column file_path does not exist in datasets table")
            file_path_exists = False
            
        # Check if preview_data column exists
        try:
            db.execute(text("SELECT preview_data FROM datasets LIMIT 1"))
            logger.info("Column preview_data already exists in datasets table")
            preview_data_exists = True
        except Exception:
            logger.info("Column preview_data does not exist in datasets table")
            preview_data_exists = False
            
        # Check if schema_metadata column exists
        try:
            db.execute(text("SELECT schema_metadata FROM datasets LIMIT 1"))
            logger.info("Column schema_metadata already exists in datasets table")
            schema_metadata_exists = True
        except Exception:
            logger.info("Column schema_metadata does not exist in datasets table")
            schema_metadata_exists = False
            
        # Check if quality_metrics column exists
        try:
            db.execute(text("SELECT quality_metrics FROM datasets LIMIT 1"))
            logger.info("Column quality_metrics already exists in datasets table")
            quality_metrics_exists = True
        except Exception:
            logger.info("Column quality_metrics does not exist in datasets table")
            quality_metrics_exists = False
            
        # Check if column_statistics column exists
        try:
            db.execute(text("SELECT column_statistics FROM datasets LIMIT 1"))
            logger.info("Column column_statistics already exists in datasets table")
            column_statistics_exists = True
        except Exception:
            logger.info("Column column_statistics does not exist in datasets table")
            column_statistics_exists = False
            
        # Check if download_count column exists
        try:
            db.execute(text("SELECT download_count FROM datasets LIMIT 1"))
            logger.info("Column download_count already exists in datasets table")
            download_count_exists = True
        except Exception:
            logger.info("Column download_count does not exist in datasets table")
            download_count_exists = False
            
        # Check if last_downloaded_at column exists
        try:
            db.execute(text("SELECT last_downloaded_at FROM datasets LIMIT 1"))
            logger.info("Column last_downloaded_at already exists in datasets table")
            last_downloaded_at_exists = True
        except Exception:
            logger.info("Column last_downloaded_at does not exist in datasets table")
            last_downloaded_at_exists = False
        
        # Add missing columns
        if not file_path_exists:
            db.execute(text("ALTER TABLE datasets ADD COLUMN file_path VARCHAR"))
            logger.info("Added file_path column to datasets table")
            
        if not preview_data_exists:
            db.execute(text("ALTER TABLE datasets ADD COLUMN preview_data JSON"))
            logger.info("Added preview_data column to datasets table")
            
        if not schema_metadata_exists:
            db.execute(text("ALTER TABLE datasets ADD COLUMN schema_metadata JSON"))
            logger.info("Added schema_metadata column to datasets table")
            
        if not quality_metrics_exists:
            db.execute(text("ALTER TABLE datasets ADD COLUMN quality_metrics JSON"))
            logger.info("Added quality_metrics column to datasets table")
            
        if not column_statistics_exists:
            db.execute(text("ALTER TABLE datasets ADD COLUMN column_statistics JSON"))
            logger.info("Added column_statistics column to datasets table")
            
        if not download_count_exists:
            db.execute(text("ALTER TABLE datasets ADD COLUMN download_count INTEGER DEFAULT 0"))
            logger.info("Added download_count column to datasets table")
            
        if not last_downloaded_at_exists:
            db.execute(text("ALTER TABLE datasets ADD COLUMN last_downloaded_at TIMESTAMP"))
            logger.info("Added last_downloaded_at column to datasets table")
        
        # Commit the changes
        db.commit()
        logger.info("Migration completed successfully")
        
        return {
            "success": True,
            "message": "Migration completed successfully",
            "columns_added": {
                "file_path": not file_path_exists,
                "preview_data": not preview_data_exists,
                "schema_metadata": not schema_metadata_exists,
                "quality_metrics": not quality_metrics_exists,
                "column_statistics": not column_statistics_exists,
                "download_count": not download_count_exists,
                "last_downloaded_at": not last_downloaded_at_exists
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Migration failed: {str(e)}")
        return {
            "success": False,
            "message": f"Migration failed: {str(e)}"
        }
    finally:
        db.close()

if __name__ == "__main__":
    result = run_migration()
    print(result)