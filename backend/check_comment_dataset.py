#!/usr/bin/env python3
"""
Check Comment dataset configuration
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
import json

def check_comment_dataset():
    """Check Comment dataset configuration"""
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Find the Comment dataset
        result = session.execute(
            text("""
                SELECT name, real_connection_config, real_credentials, connector_type 
                FROM proxy_connectors 
                WHERE name LIKE '%Comment%'
                LIMIT 1
            """)
        ).fetchone()
        
        if result:
            print(f"Name: {result[0]}")
            print(f"Type: {result[3]}")
            print(f"\nConnection Config (encrypted):")
            print(result[1][:200] + "..." if len(result[1]) > 200 else result[1])
            
            # Try to decrypt and parse
            from app.services.integrated_proxy_service import integrated_proxy
            config = integrated_proxy.decrypt_credentials(result[1])
            print(f"\nDecrypted Config:")
            print(json.dumps(config, indent=2))
        else:
            print("No Comment dataset found")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_comment_dataset()