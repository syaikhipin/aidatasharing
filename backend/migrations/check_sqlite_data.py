#!/usr/bin/env python3
"""
Check SQLite Database Content
This script examines what data exists in the SQLite database.
Created: 2025-08-26
"""

import sqlite3
import logging
import os

logger = logging.getLogger(__name__)

def check_sqlite_data():
    """Check what data exists in SQLite database"""
    sqlite_path = "/Users/syaikhipin/Documents/program/simpleaisharing/storage/aishare_platform.db"
    
    if not os.path.exists(sqlite_path):
        logger.error(f"SQLite database not found at {sqlite_path}")
        return
    
    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"Found {len(tables)} tables in SQLite database:")
        
        table_data = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_data[table] = count
                
                # Show sample data for important tables
                if table in ['datasets', 'users', 'organizations', 'configurations'] and count > 0:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                    rows = cursor.fetchall()
                    
                    # Get column names
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    logger.info(f"\n📊 Table '{table}': {count} rows")
                    logger.info(f"   Columns: {columns}")
                    
                    if rows:
                        logger.info("   Sample data:")
                        for i, row in enumerate(rows, 1):
                            row_dict = dict(zip(columns, row))
                            # Show key fields only to avoid clutter
                            key_fields = {}
                            for key in ['id', 'name', 'email', 'key', 'type', 'is_active', 'created_at']:
                                if key in row_dict:
                                    key_fields[key] = row_dict[key]
                            logger.info(f"     Row {i}: {key_fields}")
                else:
                    logger.info(f"📊 Table '{table}': {count} rows")
                    
            except Exception as e:
                logger.error(f"Error checking table {table}: {e}")
                table_data[table] = f"ERROR: {e}"
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("SQLITE DATABASE SUMMARY")
        logger.info("="*60)
        
        total_rows = sum(count for count in table_data.values() if isinstance(count, int))
        non_empty_tables = [table for table, count in table_data.items() if isinstance(count, int) and count > 0]
        empty_tables = [table for table, count in table_data.items() if isinstance(count, int) and count == 0]
        
        logger.info(f"Total rows across all tables: {total_rows}")
        logger.info(f"Non-empty tables ({len(non_empty_tables)}): {non_empty_tables}")
        logger.info(f"Empty tables ({len(empty_tables)}): {empty_tables}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error connecting to SQLite database: {e}")

def main():
    """Main function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    check_sqlite_data()

if __name__ == "__main__":
    main()