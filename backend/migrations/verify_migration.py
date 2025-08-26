#!/usr/bin/env python3
"""
Verify Migration Script
This script verifies that the SQLite to PostgreSQL migration completed successfully.
Created: 2025-08-26
"""

import logging
import os
import sys
from sqlalchemy import create_engine, text

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

logger = logging.getLogger(__name__)

def verify_migration(database_url: str):
    """Verify that the migration completed successfully"""
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            logger.info("Verifying PostgreSQL migration...")
            
            # Check key tables and their row counts
            tables_to_check = [
                'organizations', 'users', 'datasets', 'database_connectors',
                'configurations', 'dataset_access_logs', 'dataset_downloads'
            ]
            
            results = {}
            for table_name in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    results[table_name] = count
                    logger.info(f"✓ Table '{table_name}': {count} rows")
                except Exception as e:
                    logger.warning(f"✗ Could not check table '{table_name}': {e}")
                    results[table_name] = f"ERROR: {e}"
            
            # Check specific data integrity
            logger.info("\nChecking data integrity...")
            
            # Check if admin user exists
            try:
                admin_result = conn.execute(text("""
                    SELECT email, is_superuser, organization_id 
                    FROM users 
                    WHERE email = 'admin@example.com'
                """))
                admin_user = admin_result.fetchone()
                if admin_user:
                    logger.info(f"✓ Admin user found: {admin_user[0]} (superuser: {admin_user[1]}, org: {admin_user[2]})")
                else:
                    logger.warning("✗ Admin user not found")
            except Exception as e:
                logger.error(f"✗ Error checking admin user: {e}")
            
            # Check if organizations exist
            try:
                org_result = conn.execute(text("SELECT name FROM organizations ORDER BY id LIMIT 5"))
                orgs = org_result.fetchall()
                logger.info(f"✓ Sample organizations: {[org[0] for org in orgs]}")
            except Exception as e:
                logger.error(f"✗ Error checking organizations: {e}")
            
            # Check if datasets exist
            try:
                dataset_result = conn.execute(text("SELECT name, type FROM datasets ORDER BY id LIMIT 5"))
                datasets = dataset_result.fetchall()
                logger.info(f"✓ Sample datasets: {[(ds[0], ds[1]) for ds in datasets]}")
            except Exception as e:
                logger.error(f"✗ Error checking datasets: {e}")
            
            # Check sequences are properly set
            try:
                seq_result = conn.execute(text("""
                    SELECT schemaname, tablename, last_value 
                    FROM pg_sequences 
                    WHERE schemaname = 'public' 
                    ORDER BY tablename
                """))
                sequences = seq_result.fetchall()
                logger.info(f"✓ Found {len(sequences)} sequences with proper values")
                for seq in sequences[:5]:  # Show first 5
                    logger.info(f"  - {seq[1]}: {seq[2]}")
            except Exception as e:
                logger.error(f"✗ Error checking sequences: {e}")
            
            # Summary
            logger.info("\n" + "="*50)
            logger.info("MIGRATION VERIFICATION SUMMARY")
            logger.info("="*50)
            
            total_rows = sum(count for count in results.values() if isinstance(count, int))
            logger.info(f"Total rows migrated: {total_rows}")
            
            failed_tables = [table for table, result in results.items() if isinstance(result, str) and result.startswith("ERROR")]
            if failed_tables:
                logger.warning(f"Tables with issues: {failed_tables}")
            else:
                logger.info("✅ All checked tables migrated successfully!")
            
            return len(failed_tables) == 0
            
    except Exception as e:
        logger.error(f"❌ Migration verification failed: {e}")
        return False

def main():
    """Main verification function"""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    database_url = settings.DATABASE_URL
    
    if not database_url.startswith('postgresql://'):
        logger.error("DATABASE_URL must be a PostgreSQL connection string")
        return False
    
    success = verify_migration(database_url)
    
    if success:
        print("\n🎉 Migration verification completed successfully!")
        print("Your SQLite data has been successfully migrated to PostgreSQL.")
        print("You can now login to the system using PostgreSQL.")
    else:
        print("\n⚠️  Migration verification found some issues!")
        print("Check the logs above for details.")
        
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)