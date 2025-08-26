#!/usr/bin/env python3
"""
Clear PostgreSQL Database Script
This script completely clears all tables from the PostgreSQL database.
Created: 2025-08-26
"""

import logging
import os
import sys
from sqlalchemy import create_engine, text, inspect

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

logger = logging.getLogger(__name__)

def clear_postgresql_database(database_url: str):
    """Completely clear all tables from PostgreSQL database"""
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            with conn.begin():
                logger.info("Dropping all tables and sequences...")
                
                # Get all table names
                inspector = inspect(engine)
                table_names = inspector.get_table_names()
                
                if table_names:
                    logger.info(f"Found {len(table_names)} tables to drop: {table_names}")
                    
                    # Disable foreign key checks temporarily
                    conn.execute(text("SET session_replication_role = 'replica';"))
                    
                    # Drop all tables
                    for table_name in table_names:
                        conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                        logger.info(f"Dropped table: {table_name}")
                    
                    # Re-enable foreign key checks
                    conn.execute(text("SET session_replication_role = 'origin';"))
                
                # Drop all sequences
                sequences_result = conn.execute(text("""
                    SELECT sequencename FROM pg_sequences 
                    WHERE schemaname = 'public'
                """))
                
                sequences = [row[0] for row in sequences_result]
                if sequences:
                    logger.info(f"Found {len(sequences)} sequences to drop: {sequences}")
                    for sequence_name in sequences:
                        conn.execute(text(f"DROP SEQUENCE IF EXISTS {sequence_name} CASCADE"))
                        logger.info(f"Dropped sequence: {sequence_name}")
                
                # Drop all functions (stored procedures)
                functions_result = conn.execute(text("""
                    SELECT proname FROM pg_proc 
                    WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                """))
                
                functions = [row[0] for row in functions_result]
                if functions:
                    logger.info(f"Found {len(functions)} functions to drop: {functions}")
                    for function_name in functions:
                        try:
                            conn.execute(text(f"DROP FUNCTION IF EXISTS {function_name} CASCADE"))
                            logger.info(f"Dropped function: {function_name}")
                        except Exception as e:
                            logger.warning(f"Could not drop function {function_name}: {e}")
                
                logger.info("✅ PostgreSQL database cleared successfully!")
                return True
                
    except Exception as e:
        logger.error(f"❌ Failed to clear PostgreSQL database: {e}")
        return False

def main():
    """Main function"""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    database_url = settings.DATABASE_URL
    
    if not database_url.startswith('postgresql://'):
        logger.error("DATABASE_URL must be a PostgreSQL connection string")
        return False
    
    logger.info("Starting PostgreSQL database cleanup...")
    success = clear_postgresql_database(database_url)
    
    if success:
        print("✅ PostgreSQL database cleared successfully!")
        print("The database is now empty and ready for migration.")
    else:
        print("❌ Failed to clear PostgreSQL database!")
        return False
        
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)