#!/usr/bin/env python3
"""
Quick RLS fix for PostgreSQL - applies essential RLS policies only
"""

import logging
import os
import psycopg2
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def apply_quick_rls_fixes():
    """Apply essential RLS fixes quickly"""
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not found")
        return False
    
    try:
        # Connect directly with psycopg2 for better control
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        # List of tables to enable RLS on
        tables = [
            'schema_migrations',
            'configurations', 
            'system_metrics',
            'configuration_overrides',
            'mindsdb_configurations',
            'configuration_history',
            'organizations',
            'mindsdb_handlers',
            'users',
            'datasets',
            'dataset_files',
            'database_connectors'
        ]
        
        print("🔒 Enabling RLS on tables...")
        for table in tables:
            try:
                # Check if table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    )
                """, (table,))
                
                if cur.fetchone()[0]:
                    # Enable RLS
                    cur.execute(f'ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY')
                    print(f"  ✅ {table}")
                else:
                    print(f"  ⚠️  {table} (table not found)")
                    
            except Exception as e:
                print(f"  ❌ {table}: {e}")
                continue
        
        # Create a simple default deny policy for system tables
        system_tables = ['schema_migrations', 'system_metrics', 'configuration_overrides', 
                        'mindsdb_configurations', 'configuration_history', 'mindsdb_handlers']
        
        print("\n🛡️  Creating basic security policies...")
        for table in system_tables:
            try:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    )
                """, (table,))
                
                if cur.fetchone()[0]:
                    # Drop existing policy if exists
                    try:
                        cur.execute(f'DROP POLICY IF EXISTS system_deny_all ON public.{table}')
                    except:
                        pass
                    
                    # Create deny all policy for system tables
                    cur.execute(f'CREATE POLICY system_deny_all ON public.{table} FOR ALL USING (false)')
                    print(f"  🛡️  {table} - system access only")
                    
            except Exception as e:
                print(f"  ❌ Policy for {table}: {e}")
                continue
        
        # Allow read access to configurations
        try:
            cur.execute('DROP POLICY IF EXISTS config_read_allow ON public.configurations')
            cur.execute('CREATE POLICY config_read_allow ON public.configurations FOR SELECT USING (true)')
            print("  📖 configurations - read access enabled")
        except Exception as e:
            print(f"  ❌ Config read policy: {e}")
        
        # Basic organization access
        try:
            cur.execute('DROP POLICY IF EXISTS org_read_allow ON public.organizations')
            cur.execute('CREATE POLICY org_read_allow ON public.organizations FOR SELECT USING (true)')
            print("  🏢 organizations - read access enabled")
        except Exception as e:
            print(f"  ❌ Org read policy: {e}")
        
        cur.close()
        conn.close()
        
        print("\n✅ Quick RLS fixes applied successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to apply RLS fixes: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    apply_quick_rls_fixes()