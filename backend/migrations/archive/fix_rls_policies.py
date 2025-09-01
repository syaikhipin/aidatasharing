#!/usr/bin/env python3
"""
Fix RLS policies for tables with specific column structures
"""

import logging
import os
import psycopg2
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def fix_rls_policies():
    """Fix RLS policies for tables with specific issues"""
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not found")
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("🔧 Fixing RLS policies for specific tables...")
        
        # Tables with user_id column (not owner_id)
        user_id_tables = [
            'user_session_logs', 'activity_logs', 'dataset_access_logs', 
            'dataset_downloads', 'file_uploads', 'dataset_access'
        ]
        
        for table in user_id_tables:
            try:
                cur.execute(f'DROP POLICY IF EXISTS user_data_policy ON public.{table}')
                cur.execute(f"""
                    CREATE POLICY user_access ON public.{table} 
                    FOR ALL USING (user_id = current_setting('app.current_user_id', true)::integer)
                """)
                print(f"  ✅ {table} - user_id policy fixed")
            except Exception as e:
                print(f"  ❌ {table}: {e}")
        
        # Tables that need basic restrictive policy
        restrictive_tables = ['notifications', 'access_requests']
        
        for table in restrictive_tables:
            try:
                cur.execute(f'DROP POLICY IF EXISTS user_data_policy ON public.{table}')
                cur.execute(f"""
                    CREATE POLICY restrictive_access ON public.{table} 
                    FOR ALL USING (false)
                """)
                print(f"  🛡️  {table} - restrictive policy applied")
            except Exception as e:
                print(f"  ❌ {table}: {e}")
        
        # Dataset-related tables - fix enum issue
        dataset_tables = [
            'dataset_models', 'dataset_chat_sessions', 'dataset_share_accesses',
            'share_access_sessions', 'chat_interactions', 'chat_messages'
        ]
        
        for table in dataset_tables:
            try:
                cur.execute(f'DROP POLICY IF EXISTS dataset_data_policy ON public.{table}')
                
                # Check if table has dataset_id column
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = %s AND column_name = 'dataset_id'
                    )
                """, (table,))
                
                has_dataset_id = cur.fetchone()[0]
                
                if has_dataset_id:
                    cur.execute(f"""
                        CREATE POLICY dataset_access ON public.{table} 
                        FOR ALL USING (
                            dataset_id IN (
                                SELECT id FROM datasets WHERE 
                                owner_id = current_setting('app.current_user_id', true)::integer 
                                OR organization_id = current_setting('app.current_org_id', true)::integer
                                OR sharing_level::text = 'public'
                            )
                        )
                    """)
                else:
                    # If no dataset_id, apply restrictive policy
                    cur.execute(f"""
                        CREATE POLICY restrictive_access ON public.{table} 
                        FOR ALL USING (false)
                    """)
                
                print(f"  ✅ {table} - dataset policy fixed")
            except Exception as e:
                print(f"  ❌ {table}: {e}")
        
        cur.close()
        conn.close()
        
        print("\n✅ RLS policy fixes completed!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix RLS policies: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fix_rls_policies()