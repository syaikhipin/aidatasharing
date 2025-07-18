"""Add document support fields to datasets table

Revision ID: 20250717_160000
Creates Date: 2025-07-17 16:00:00
"""

import logging

logger = logging.getLogger(__name__)


def upgrade(cursor):
    """Add document support fields to datasets table"""
    logger.info("Starting document support migration...")
    
    # Add document-specific columns
    try:
        cursor.execute("ALTER TABLE datasets ADD COLUMN document_type VARCHAR")
        logger.info("Added column: document_type")
    except Exception as e:
        logger.warning(f"Failed to add document_type column: {e}")
    
    try:
        cursor.execute("ALTER TABLE datasets ADD COLUMN page_count INTEGER")
        logger.info("Added column: page_count")
    except Exception as e:
        logger.warning(f"Failed to add page_count column: {e}")
    
    try:
        cursor.execute("ALTER TABLE datasets ADD COLUMN word_count INTEGER")
        logger.info("Added column: word_count")
    except Exception as e:
        logger.warning(f"Failed to add word_count column: {e}")
    
    try:
        cursor.execute("ALTER TABLE datasets ADD COLUMN extracted_text TEXT")
        logger.info("Added column: extracted_text")
    except Exception as e:
        logger.warning(f"Failed to add extracted_text column: {e}")
    
    try:
        cursor.execute("ALTER TABLE datasets ADD COLUMN text_extraction_method VARCHAR")
        logger.info("Added column: text_extraction_method")
    except Exception as e:
        logger.warning(f"Failed to add text_extraction_method column: {e}")
    
    logger.info("Document support migration completed successfully")


def downgrade(cursor):
    """Remove document support fields from datasets table"""
    logger.info("Downgrading document support migration...")
    
    # Remove document-specific columns
    try:
        cursor.execute("ALTER TABLE datasets DROP COLUMN document_type")
        cursor.execute("ALTER TABLE datasets DROP COLUMN page_count")
        cursor.execute("ALTER TABLE datasets DROP COLUMN word_count")
        cursor.execute("ALTER TABLE datasets DROP COLUMN extracted_text")
        cursor.execute("ALTER TABLE datasets DROP COLUMN text_extraction_method")
        logger.info("Removed document-specific columns")
    except Exception as e:
        logger.warning(f"Failed to remove document-specific columns: {e}")
    
    logger.info("Document support migration downgrade completed")