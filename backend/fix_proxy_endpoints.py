#!/usr/bin/env python3
"""
Fix proxy connectors that are missing endpoints
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(backend_dir))

# Load environment variables
from dotenv import load_dotenv
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.proxy_connector import ProxyConnector
from app.services.unified_proxy_service import unified_proxy
import json

def fix_proxy_endpoints():
    """Fix proxy connectors with missing endpoints"""
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("🔧 Fixing proxy connector endpoints...")
        
        # Find API proxy connectors
        proxy_connectors = session.query(ProxyConnector).filter(
            ProxyConnector.connector_type == "api",
            ProxyConnector.is_active == True
        ).all()
        
        fixed_count = 0
        
        for connector in proxy_connectors:
            try:
                # Get the configuration (might be encrypted or plain JSON)
                if isinstance(connector.real_connection_config, str):
                    try:
                        # Try to parse as JSON first (not encrypted)
                        config = json.loads(connector.real_connection_config)
                    except json.JSONDecodeError:
                        # If not JSON, try to decrypt
                        config = unified_proxy.decrypt_credentials(connector.real_connection_config)
                else:
                    config = connector.real_connection_config
                
                # Check if endpoint is missing or is root
                current_endpoint = config.get('endpoint', '/')
                
                if current_endpoint == '/' or not current_endpoint:
                    # Try to detect endpoint from name or source_url
                    name_lower = connector.name.lower()
                    new_endpoint = '/'
                    
                    # Check source_url first
                    if config.get('source_url'):
                        source_url = config['source_url']
                        if source_url.count('/') > 2:
                            url_parts = source_url.split('/', 3)
                            if len(url_parts) > 3:
                                new_endpoint = '/' + url_parts[3]
                                print(f"  📍 Detected endpoint from source_url for {connector.name}: {new_endpoint}")
                    
                    # If still root, try to infer from name
                    if new_endpoint == '/':
                        if 'comment' in name_lower:
                            new_endpoint = '/comments'
                        elif 'album' in name_lower:
                            new_endpoint = '/albums'
                        elif 'photo' in name_lower:
                            new_endpoint = '/photos'
                        elif 'post' in name_lower:
                            new_endpoint = '/posts'
                        elif 'user' in name_lower:
                            new_endpoint = '/users'
                        elif 'todo' in name_lower:
                            new_endpoint = '/todos'
                        
                        if new_endpoint != '/':
                            print(f"  🎯 Inferred endpoint from name for {connector.name}: {new_endpoint}")
                    
                    # Update configuration if we found an endpoint
                    if new_endpoint != '/':
                        config['endpoint'] = new_endpoint
                        config['dataset_endpoint'] = new_endpoint  # Store as dataset_endpoint too
                        
                        # Save back as JSON
                        connector.real_connection_config = json.dumps(config)
                        fixed_count += 1
                        print(f"  ✅ Fixed {connector.name}: endpoint set to {new_endpoint}")
                    else:
                        print(f"  ⚠️ Could not determine endpoint for {connector.name}")
                else:
                    print(f"  ✓ {connector.name} already has endpoint: {current_endpoint}")
                    
            except Exception as e:
                print(f"  ❌ Error processing {connector.name}: {e}")
        
        # Commit all changes
        session.commit()
        print(f"\n✅ Fixed {fixed_count} proxy connectors")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    fix_proxy_endpoints()