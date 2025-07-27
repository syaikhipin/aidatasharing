"""
Migration to update proxy connector URLs to use new high ports (above 10100)
"""

import sqlite3
import json
import re
from datetime import datetime

def update_proxy_connector_ports():
    """Update existing proxy connector configurations to use new high ports"""
    
    # Port mapping from old to new
    port_mapping = {
        '8080': '10103',  # API
        '8081': '10102',  # PostgreSQL
        '8082': '10103',  # API (alternative)
        '8083': '10104',  # ClickHouse
        '8084': '10105',  # MongoDB
        '8085': '10106',  # S3
        '8086': '10107',  # Shared Links
        '3307': '10101',  # MySQL
        '5433': '10102',  # PostgreSQL (alternative)
        '9000': '10104',  # ClickHouse (alternative)
        '27018': '10105', # MongoDB (alternative)
        '9001': '10106',  # S3 (alternative)
    }
    
    try:
        # Connect to the database
        conn = sqlite3.connect('storage/aishare_platform.db')
        cursor = conn.cursor()
        
        print("🔄 Starting proxy connector port migration...")
        
        # Check if proxy_connectors table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='proxy_connectors'
        """)
        
        if not cursor.fetchone():
            print("ℹ️  No proxy_connectors table found - skipping migration")
            conn.close()
            return
        
        # Get all proxy connectors
        cursor.execute("""
            SELECT id, proxy_url, real_connection_config, real_credentials
            FROM proxy_connectors
            WHERE is_active = 1
        """)
        
        connectors = cursor.fetchall()
        updated_count = 0
        
        for connector_id, proxy_url, real_config_json, real_creds_json in connectors:
            updated = False
            
            # Update proxy_url
            new_proxy_url = proxy_url
            for old_port, new_port in port_mapping.items():
                if f":{old_port}" in proxy_url:
                    new_proxy_url = proxy_url.replace(f":{old_port}", f":{new_port}")
                    updated = True
                    break
            
            # Update real_connection_config if it contains port references
            new_real_config = real_config_json
            if real_config_json:
                try:
                    # Try to parse as JSON (if it's encrypted, this will fail gracefully)
                    config = json.loads(real_config_json)
                    if isinstance(config, dict) and 'port' in config:
                        old_port = str(config['port'])
                        if old_port in port_mapping:
                            config['port'] = int(port_mapping[old_port])
                            new_real_config = json.dumps(config)
                            updated = True
                except (json.JSONDecodeError, TypeError):
                    # If it's encrypted or not JSON, update string references
                    for old_port, new_port in port_mapping.items():
                        if old_port in real_config_json:
                            new_real_config = real_config_json.replace(old_port, new_port)
                            updated = True
            
            # Update real_credentials if it contains port references
            new_real_creds = real_creds_json
            if real_creds_json:
                try:
                    # Try to parse as JSON (if it's encrypted, this will fail gracefully)
                    creds = json.loads(real_creds_json)
                    if isinstance(creds, dict) and 'port' in creds:
                        old_port = str(creds['port'])
                        if old_port in port_mapping:
                            creds['port'] = int(port_mapping[old_port])
                            new_real_creds = json.dumps(creds)
                            updated = True
                except (json.JSONDecodeError, TypeError):
                    # If it's encrypted or not JSON, update string references
                    for old_port, new_port in port_mapping.items():
                        if old_port in real_creds_json:
                            new_real_creds = real_creds_json.replace(old_port, new_port)
                            updated = True
            
            # Update the record if any changes were made
            if updated:
                cursor.execute("""
                    UPDATE proxy_connectors 
                    SET proxy_url = ?, 
                        real_connection_config = ?, 
                        real_credentials = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (new_proxy_url, new_real_config, new_real_creds, datetime.utcnow(), connector_id))
                
                updated_count += 1
                print(f"✅ Updated proxy connector {connector_id}")
                print(f"   Old URL: {proxy_url}")
                print(f"   New URL: {new_proxy_url}")
        
        # Update shared_proxy_links table
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='shared_proxy_links'
        """)
        
        if cursor.fetchone():
            cursor.execute("""
                SELECT id, public_url
                FROM shared_proxy_links
                WHERE is_active = 1
            """)
            
            shared_links = cursor.fetchall()
            
            for link_id, public_url in shared_links:
                new_public_url = public_url
                updated = False
                
                for old_port, new_port in port_mapping.items():
                    if f":{old_port}" in public_url:
                        new_public_url = public_url.replace(f":{old_port}", f":{new_port}")
                        updated = True
                        break
                
                if updated:
                    cursor.execute("""
                        UPDATE shared_proxy_links 
                        SET public_url = ?, updated_at = ?
                        WHERE id = ?
                    """, (new_public_url, datetime.utcnow(), link_id))
                    
                    updated_count += 1
                    print(f"✅ Updated shared link {link_id}")
                    print(f"   Old URL: {public_url}")
                    print(f"   New URL: {new_public_url}")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print(f"🎉 Migration completed! Updated {updated_count} records")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise

if __name__ == "__main__":
    update_proxy_connector_ports()