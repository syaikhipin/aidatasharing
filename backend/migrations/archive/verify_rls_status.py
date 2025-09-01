#!/usr/bin/env python3
"""
Verify RLS status for all tables
"""

import logging
import os
import psycopg2
from dotenv import load_dotenv

def verify_rls_status():
    """Verify RLS is enabled on all public tables"""
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not found")
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Get all public tables and their RLS status
        cur.execute("""
            SELECT 
                pt.tablename,
                pc.relrowsecurity as rls_enabled,
                COUNT(pp.polname) as policy_count
            FROM pg_tables pt
            LEFT JOIN pg_class pc ON pc.relname = pt.tablename
            LEFT JOIN pg_policy pp ON pp.polrelid = pc.oid
            WHERE pt.schemaname = 'public'
            GROUP BY pt.tablename, pc.relrowsecurity
            ORDER BY pt.tablename
        """)
        
        results = cur.fetchall()
        
        print("📊 RLS Status Summary for all public tables:")
        print("=" * 60)
        
        enabled_count = 0
        total_count = len(results)
        
        for table_name, rls_enabled, policy_count in results:
            status = "✅ ENABLED" if rls_enabled else "❌ DISABLED"
            policies = f"({policy_count} policies)" if policy_count > 0 else "(no policies)"
            
            print(f"{table_name:<30} {status:<12} {policies}")
            
            if rls_enabled:
                enabled_count += 1
        
        print("=" * 60)
        print(f"Summary: {enabled_count}/{total_count} tables have RLS enabled")
        
        if enabled_count == total_count:
            print("🎉 All tables now have RLS enabled!")
        else:
            print(f"⚠️  {total_count - enabled_count} tables still need RLS enabled")
        
        cur.close()
        conn.close()
        
        return enabled_count == total_count
        
    except Exception as e:
        print(f"❌ Failed to verify RLS status: {e}")
        return False

if __name__ == "__main__":
    verify_rls_status()