#!/usr/bin/env python3
"""
Clean up migration files - keep only essential ones
"""

import os
import shutil
from pathlib import Path

def clean_migration_files():
    """Clean up migration files, keeping only essential ones"""
    
    migrations_dir = Path(__file__).parent
    
    # Essential files to keep
    essential_files = {
        '__init__.py',  # Python package file
        'consolidated_migration_postgresql.py',  # Main schema migration
        'clean_migrations.py',  # This cleanup script
    }
    
    # Files to archive (old/redundant files)
    files_to_archive = [
        'apply_rls_fixes.py',
        'quick_rls_fix.py', 
        'complete_rls_fix.py',
        'fix_rls_policies.py',
        'verify_rls_status.py',
        'sqlite_to_postgresql_migration.py',
        'check_sqlite_data.py',
        'verify_migration.py',
        'clear_postgresql_database.py',
        'postgresql_migration_manager.py',
        'fix_user_roles.py',
        'fix_all_sequences.py',
        'test_migration_fixes.py',
        'fix_sharing_enabled.py',
        'enable_rls.sql'
    ]
    
    # Create archive directory
    archive_dir = migrations_dir / 'archive'
    archive_dir.mkdir(exist_ok=True)
    
    print("🧹 Cleaning up migration files...")
    
    # Move files to archive
    archived_count = 0
    for filename in files_to_archive:
        file_path = migrations_dir / filename
        if file_path.exists():
            archive_path = archive_dir / filename
            shutil.move(str(file_path), str(archive_path))
            print(f"  📦 Archived: {filename}")
            archived_count += 1
    
    # List remaining files
    print(f"\n✅ Migration cleanup completed!")
    print(f"📊 {archived_count} files archived")
    
    remaining_files = [f.name for f in migrations_dir.iterdir() 
                      if f.is_file() and f.name.endswith(('.py', '.sql'))]
    
    print(f"\n📋 Essential migration files remaining:")
    for filename in sorted(remaining_files):
        print(f"  • {filename}")
    
    # Create a simple RLS management script
    create_rls_management_script(migrations_dir)
    
    return True

def create_rls_management_script(migrations_dir):
    """Create a consolidated RLS management script"""
    
    rls_script_content = '''#!/usr/bin/env python3
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
        
        print("\\n✅ RLS enabled on all tables!")
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
'''
    
    rls_script_path = migrations_dir / 'rls_manager.py'
    with open(rls_script_path, 'w') as f:
        f.write(rls_script_content)
    
    print(f"  ✨ Created: rls_manager.py")

if __name__ == "__main__":
    clean_migration_files()