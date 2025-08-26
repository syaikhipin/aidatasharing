#!/usr/bin/env python3
"""
Fix User Roles Migration
Ensures all users have proper role values and sets up constraints.
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

def fix_user_roles():
    """Fix user roles in the database"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        with conn.begin():
            try:
                logger.info("Fixing user roles...")
                
                # Update all NULL roles to proper defaults
                result = conn.execute(text("""
                    UPDATE users 
                    SET role = CASE 
                        WHEN is_superuser = true THEN 'admin'
                        ELSE 'member'
                    END
                    WHERE role IS NULL
                """))
                
                logger.info(f"Updated {result.rowcount} users with default roles")
                
                # Set default value for the role column to prevent future NULL values
                try:
                    conn.execute(text("""
                        ALTER TABLE users 
                        ALTER COLUMN role SET DEFAULT 'member'
                    """))
                    logger.info("Set default value for role column")
                except Exception as e:
                    logger.warning(f"Could not set default for role column: {e}")
                
                # Add check constraint to ensure role is not NULL
                try:
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD CONSTRAINT chk_users_role_not_null 
                        CHECK (role IS NOT NULL)
                    """))
                    logger.info("Added NOT NULL constraint to role column")
                except Exception as e:
                    logger.warning(f"Could not add NOT NULL constraint to role column: {e}")
                
                return True
                
            except Exception as e:
                logger.error(f"Error fixing user roles: {e}")
                return False

def main():
    """Main function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = fix_user_roles()
    
    if success:
        print("✅ User roles fixed successfully!")
    else:
        print("❌ Failed to fix user roles!")
        sys.exit(1)

if __name__ == "__main__":
    main()