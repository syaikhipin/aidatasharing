#!/usr/bin/env python3
"""
Row Level Security (RLS) Management Script
Consolidated script for managing PostgreSQL RLS policies
"""

import logging
import os
import psycopg2
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def enable_rls_on_all_tables():
    """Enable RLS on all public schema tables"""
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not found")
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Get all public tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cur.fetchall()]
        
        print(f"🔒 Enabling RLS on {len(tables)} tables...")
        
        for table in tables:
            try:
                # Enable RLS
                cur.execute(f'ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY')
                
                # Create basic restrictive policy if none exists
                cur.execute(f"""
                    SELECT COUNT(*) FROM pg_policy 
                    WHERE polrelid = 'public.{table}'::regclass
                """)
                
                policy_count = cur.fetchone()[0]
                if policy_count == 0:
                    cur.execute(f'CREATE POLICY default_policy ON public.{table} FOR ALL USING (false)')
                
                print(f"  ✅ {table}")
                
            except Exception as e:
                print(f"  ❌ {table}: {e}")
        
        cur.close()
        conn.close()
        
        print("\n✅ RLS enabled on all tables!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to enable RLS: {e}")
        return False

def verify_rls_status():
    """Verify RLS status for all public tables"""
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not found")
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                t.table_name,
                c.relrowsecurity
            FROM information_schema.tables t
            LEFT JOIN pg_class c ON c.relname = t.table_name
            WHERE t.table_schema = 'public'
            AND t.table_type = 'BASE TABLE'
            ORDER BY t.table_name
        """)
        
        results = cur.fetchall()
        
        print('🔐 RLS Status for all public tables:')
        print('=' * 50)
        
        enabled_count = 0
        for table_name, rls_enabled in results:
            status = '✅' if rls_enabled else '❌'
            print(f'{status} {table_name}')
            if rls_enabled:
                enabled_count += 1
        
        print('=' * 50)
        print(f'Summary: {enabled_count}/{len(results)} tables have RLS enabled')
        
        cur.close()
        conn.close()
        
        return enabled_count == len(results)
        
    except Exception as e:
        print(f"❌ Failed to verify RLS status: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "enable":
            enable_rls_on_all_tables()
        elif sys.argv[1] == "verify":
            verify_rls_status()
        else:
            print("Usage: python rls_manager.py [enable|verify]")
    else:
        print("RLS Management Script")
        print("Usage: python rls_manager.py [enable|verify]")
