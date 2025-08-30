#!/usr/bin/env python3
"""
Fix All PostgreSQL Sequences
This script fixes all sequence values to match the existing data.
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

def fix_all_sequences():
    """Fix all PostgreSQL sequences to match existing data"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        with conn.begin():
            try:
                logger.info("Checking and fixing all PostgreSQL sequences...")
                
                # Get all sequences
                sequences_result = conn.execute(text("""
                    SELECT schemaname, sequencename, last_value 
                    FROM pg_sequences 
                    WHERE schemaname = 'public'
                    ORDER BY sequencename
                """))
                
                sequences = sequences_result.fetchall()
                fixed_count = 0
                
                for seq in sequences:
                    schema, seq_name, last_value = seq
                    
                    # Extract table name from sequence name (remove _id_seq suffix)
                    if seq_name.endswith('_id_seq'):
                        table_name = seq_name[:-7]  # Remove '_id_seq'
                        
                        try:
                            # Check if table exists and has an id column
                            check_table = conn.execute(text(f"""
                                SELECT column_name 
                                FROM information_schema.columns 
                                WHERE table_name = '{table_name}' 
                                AND column_name = 'id'
                            """))
                            
                            if not check_table.fetchone():
                                logger.info(f"Skipping {table_name}: no id column")
                                continue
                            
                            # Check max ID in the corresponding table
                            max_result = conn.execute(text(f'SELECT MAX(id) FROM {table_name}'))
                            max_id_row = max_result.fetchone()
                            max_id = max_id_row[0] if max_id_row and max_id_row[0] is not None else 0
                            
                            if max_id > last_value:
                                logger.info(f"Fixing {table_name}: sequence={last_value}, max_id={max_id}")
                                
                                # Fix the sequence
                                conn.execute(text(f"SELECT setval('{seq_name}', {max_id})"))
                                fixed_count += 1
                                logger.info(f"  ✅ Fixed {seq_name} to {max_id}")
                            else:
                                logger.info(f"OK {table_name}: sequence={last_value}, max_id={max_id}")
                                
                        except Exception as e:
                            logger.warning(f"Could not check table {table_name}: {e}")
                    else:
                        logger.info(f"Skipping {seq_name}: non-standard sequence name")
                
                logger.info(f"Fixed {fixed_count} sequences")
                return True
                
            except Exception as e:
                logger.error(f"Error fixing sequences: {e}")
                return False

def main():
    """Main function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = fix_all_sequences()
    
    if success:
        print("✅ All sequences fixed successfully!")
    else:
        print("❌ Failed to fix sequences!")
        sys.exit(1)

if __name__ == "__main__":
    main()