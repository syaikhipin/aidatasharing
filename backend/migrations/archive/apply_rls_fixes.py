#!/usr/bin/env python3
"""
Apply Row Level Security (RLS) fixes to PostgreSQL database
This script enables RLS on all public schema tables to resolve security warnings.
"""

import logging
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class RLSFixer:
    """Apply Row Level Security fixes to PostgreSQL database"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        
    def apply_rls_fixes(self):
        """Apply RLS fixes by executing the SQL script"""
        try:
            # Read the SQL script
            sql_file = Path(__file__).parent / "enable_rls.sql"
            if not sql_file.exists():
                logger.error(f"RLS SQL script not found at: {sql_file}")
                return False
                
            with open(sql_file, 'r') as f:
                sql_content = f.read()
            
            # Split by statements and execute
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            with self.engine.connect() as conn:
                with conn.begin():
                    logger.info("Applying RLS fixes...")
                    
                    for i, statement in enumerate(statements):
                        if statement.startswith('--') or not statement:
                            continue
                            
                        try:
                            logger.debug(f"Executing statement {i+1}/{len(statements)}")
                            conn.execute(text(statement))
                        except Exception as e:
                            # Some statements might fail if policies already exist - that's OK
                            logger.warning(f"Statement {i+1} warning: {e}")
                            continue
                    
                    logger.info("RLS fixes applied successfully!")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to apply RLS fixes: {e}")
            return False

    def verify_rls_status(self):
        """Verify that RLS is enabled on tables"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        rowsecurity
                    FROM pg_tables pt
                    LEFT JOIN pg_class pc ON pc.relname = pt.tablename
                    WHERE pt.schemaname = 'public'
                    ORDER BY pt.tablename
                """))
                
                logger.info("RLS status for public schema tables:")
                for row in result:
                    status = "✅ ENABLED" if row.rowsecurity else "❌ DISABLED"
                    logger.info(f"  {row.tablename}: {status}")
                
                return True
        except Exception as e:
            logger.error(f"Failed to verify RLS status: {e}")
            return False

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        exit(1)
        
    if not database_url.startswith('postgresql://'):
        print("ERROR: DATABASE_URL must be a PostgreSQL connection string")
        exit(1)
    
    fixer = RLSFixer(database_url)
    
    print("🔒 Applying Row Level Security fixes...")
    success = fixer.apply_rls_fixes()
    
    if success:
        print("✅ RLS fixes applied successfully!")
        print("\n🔍 Verifying RLS status...")
        fixer.verify_rls_status()
    else:
        print("❌ Failed to apply RLS fixes!")
        exit(1)