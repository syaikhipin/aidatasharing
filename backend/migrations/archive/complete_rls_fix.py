#!/usr/bin/env python3
"""
Complete RLS fix for all remaining PostgreSQL tables
"""

import logging
import os
import psycopg2
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def apply_complete_rls_fixes():
    """Apply RLS fixes to all remaining tables"""
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not found")
        return False
    
    try:
        # Connect directly with psycopg2
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Additional tables that need RLS
        additional_tables = [
            'datashare_stats',
            'llm_configurations', 
            'activity_logs',
            'usage_metrics',
            'user_session_logs',
            'notifications',
            'proxy_connectors',
            'proxy_credential_vault',
            'shared_proxy_links',
            'dataset_access_logs',
            'dataset_downloads',
            'dataset_models',
            'dataset_chat_sessions',
            'dataset_share_accesses',
            'share_access_sessions',
            'file_uploads',
            'dataset_access',
            'chat_interactions',
            'api_usage',
            'usage_stats',
            'access_requests',
            'audit_logs',
            'proxy_access_logs',
            'chat_messages',
            'file_processing_logs',
            'model_performance_logs'
        ]
        
        print(f"🔒 Enabling RLS on {len(additional_tables)} additional tables...")
        success_count = 0
        
        for table in additional_tables:
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
                    success_count += 1
                else:
                    print(f"  ⚠️  {table} (table not found)")
                    
            except Exception as e:
                print(f"  ❌ {table}: {e}")
                continue
        
        print(f"\n🛡️  Creating security policies for {success_count} tables...")
        
        # Create appropriate policies for different table types
        policy_groups = {
            # User-related data - users can access their own data
            'user_data': [
                'user_session_logs', 'notifications', 'activity_logs', 
                'dataset_access_logs', 'dataset_downloads', 'file_uploads',
                'dataset_access', 'access_requests'
            ],
            
            # Dataset-related data - based on dataset ownership/sharing
            'dataset_data': [
                'dataset_models', 'dataset_chat_sessions', 'dataset_share_accesses',
                'share_access_sessions', 'chat_interactions', 'chat_messages'
            ],
            
            # System/Admin data - restrictive access
            'system_data': [
                'datashare_stats', 'usage_metrics', 'usage_stats', 'api_usage',
                'audit_logs', 'file_processing_logs', 'model_performance_logs'
            ],
            
            # Configuration data - read-only for most users
            'config_data': [
                'llm_configurations'
            ],
            
            # Proxy/Security data - very restrictive
            'proxy_data': [
                'proxy_connectors', 'proxy_credential_vault', 'shared_proxy_links', 
                'proxy_access_logs'
            ]
        }
        
        # Apply policies based on data type
        for group, tables in policy_groups.items():
            for table in tables:
                try:
                    # Check if table exists first
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = %s
                        )
                    """, (table,))
                    
                    if not cur.fetchone()[0]:
                        continue
                    
                    # Drop existing policies
                    try:
                        cur.execute(f'DROP POLICY IF EXISTS {group}_policy ON public.{table}')
                    except:
                        pass
                    
                    if group == 'user_data':
                        # Users can access their own data
                        cur.execute(f"""
                            CREATE POLICY {group}_policy ON public.{table} 
                            FOR ALL USING (
                                CASE 
                                    WHEN EXISTS(SELECT 1 FROM information_schema.columns 
                                               WHERE table_name = '{table}' AND column_name = 'user_id')
                                    THEN user_id = current_setting('app.current_user_id', true)::integer
                                    WHEN EXISTS(SELECT 1 FROM information_schema.columns 
                                               WHERE table_name = '{table}' AND column_name = 'owner_id')
                                    THEN owner_id = current_setting('app.current_user_id', true)::integer
                                    ELSE false
                                END
                            )
                        """)
                        
                    elif group == 'dataset_data':
                        # Access based on dataset ownership/sharing
                        cur.execute(f"""
                            CREATE POLICY {group}_policy ON public.{table} 
                            FOR ALL USING (
                                CASE 
                                    WHEN EXISTS(SELECT 1 FROM information_schema.columns 
                                               WHERE table_name = '{table}' AND column_name = 'dataset_id')
                                    THEN dataset_id IN (
                                        SELECT id FROM datasets WHERE 
                                        owner_id = current_setting('app.current_user_id', true)::integer 
                                        OR organization_id = current_setting('app.current_org_id', true)::integer
                                        OR sharing_level = 'public'
                                    )
                                    ELSE false
                                END
                            )
                        """)
                        
                    elif group == 'config_data':
                        # Read-only access
                        cur.execute(f"""
                            CREATE POLICY {group}_policy ON public.{table} 
                            FOR SELECT USING (true)
                        """)
                        cur.execute(f"""
                            CREATE POLICY {group}_write_deny ON public.{table} 
                            FOR INSERT WITH CHECK (false)
                        """)
                        
                    else:  # system_data and proxy_data
                        # Very restrictive - deny all public access
                        cur.execute(f"""
                            CREATE POLICY {group}_policy ON public.{table} 
                            FOR ALL USING (false)
                        """)
                    
                    print(f"  🛡️  {table} - {group} policy applied")
                    
                except Exception as e:
                    print(f"  ❌ Policy for {table}: {e}")
                    continue
        
        cur.close()
        conn.close()
        
        print(f"\n✅ Complete RLS fixes applied successfully!")
        print(f"📊 {success_count} tables now have RLS enabled with appropriate policies")
        return True
        
    except Exception as e:
        print(f"❌ Failed to apply complete RLS fixes: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    apply_complete_rls_fixes()