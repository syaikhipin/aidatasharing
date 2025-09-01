#!/usr/bin/env python3
"""
Migration script to fix public_share_enabled flag for datasets with non-private sharing levels.
This ensures datasets with 'organization' or 'public' sharing levels are properly marked as shared.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.dataset import Dataset, DataSharingLevel
import secrets
import string

def generate_share_token(dataset_id: int, user_id: int) -> str:
    """Generate a unique share token for a dataset."""
    # Create a base token with dataset and user info
    base_token = f"{dataset_id}_{user_id}_{secrets.token_urlsafe(16)}"
    
    # Add some random characters for extra uniqueness
    random_suffix = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
    
    return f"{base_token}_{random_suffix}"

def fix_sharing_enabled():
    """Fix public_share_enabled for datasets with non-private sharing levels."""
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("Starting migration to fix public_share_enabled flags...")
        
        # Find all datasets with non-private sharing level but public_share_enabled is False
        datasets = db.query(Dataset).filter(
            Dataset.sharing_level != DataSharingLevel.PRIVATE,
            Dataset.public_share_enabled == False,
            Dataset.is_deleted == False,
            Dataset.is_active == True
        ).all()
        
        print(f"Found {len(datasets)} datasets that need fixing")
        
        fixed_count = 0
        for dataset in datasets:
            print(f"  - Fixing dataset {dataset.id}: {dataset.name} (sharing_level: {dataset.sharing_level.value})")
            
            # Set public_share_enabled to True
            dataset.public_share_enabled = True
            
            # Generate share token if it doesn't exist
            if not dataset.share_token:
                dataset.share_token = generate_share_token(dataset.id, dataset.owner_id)
                print(f"    Generated share token: {dataset.share_token[:20]}...")
            
            # Enable AI chat by default for these datasets
            dataset.ai_chat_enabled = True
            
            fixed_count += 1
        
        # Commit all changes
        db.commit()
        print(f"\nSuccessfully fixed {fixed_count} datasets")
        
        # Now verify the fix by counting shared datasets
        shared_count = db.query(Dataset).filter(
            Dataset.public_share_enabled == True,
            Dataset.is_deleted == False,
            Dataset.is_active == True
        ).count()
        
        print(f"Total datasets with public_share_enabled=True: {shared_count}")
        
        # Show breakdown by sharing level
        for level in [DataSharingLevel.PRIVATE, DataSharingLevel.ORGANIZATION, DataSharingLevel.PUBLIC]:
            count = db.query(Dataset).filter(
                Dataset.sharing_level == level,
                Dataset.public_share_enabled == True,
                Dataset.is_deleted == False,
                Dataset.is_active == True
            ).count()
            print(f"  - {level.value}: {count} datasets")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_sharing_enabled()