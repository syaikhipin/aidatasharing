#!/usr/bin/env python3
"""
Test script to verify sharing level behavior for newly uploaded datasets.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.dataset import Dataset, DataSharingLevel

def test_sharing_levels():
    """Test sharing levels for existing datasets."""
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("Testing sharing levels for datasets...")
        
        # Get all datasets
        datasets = db.query(Dataset).filter(
            Dataset.is_deleted == False,
            Dataset.is_active == True
        ).all()
        
        print(f"\nFound {len(datasets)} active datasets:")
        print("-" * 80)
        
        for dataset in datasets:
            sharing_level = dataset.sharing_level.value if dataset.sharing_level else "None"
            public_share = "Yes" if dataset.public_share_enabled else "No"
            share_token = "Yes" if dataset.share_token else "No"
            
            print(f"ID: {dataset.id:2d} | Name: {dataset.name[:30]:30} | Level: {sharing_level:12} | Public: {public_share:3} | Token: {share_token:3}")
        
        # Test specific issues
        print("\n" + "="*80)
        print("ISSUE ANALYSIS:")
        print("="*80)
        
        # Check datasets with public sharing level but public_share_enabled = False
        problem_datasets = db.query(Dataset).filter(
            Dataset.sharing_level == DataSharingLevel.PUBLIC,
            Dataset.public_share_enabled == False,
            Dataset.is_deleted == False,
            Dataset.is_active == True
        ).all()
        
        if problem_datasets:
            print(f"\n❌ Found {len(problem_datasets)} datasets with PUBLIC sharing level but public_share_enabled=False:")
            for dataset in problem_datasets:
                print(f"   - ID {dataset.id}: {dataset.name}")
        else:
            print("\n✅ No datasets found with PUBLIC sharing level and public_share_enabled=False")
        
        # Check datasets with public_share_enabled = True but no share_token
        missing_token_datasets = db.query(Dataset).filter(
            Dataset.public_share_enabled == True,
            Dataset.share_token.is_(None),
            Dataset.is_deleted == False,
            Dataset.is_active == True
        ).all()
        
        if missing_token_datasets:
            print(f"\n❌ Found {len(missing_token_datasets)} datasets with public_share_enabled=True but no share_token:")
            for dataset in missing_token_datasets:
                print(f"   - ID {dataset.id}: {dataset.name}")
        else:
            print("\n✅ No datasets found with public_share_enabled=True and missing share_token")
        
        # Summary by sharing level
        print("\n" + "="*40)
        print("SUMMARY BY SHARING LEVEL:")
        print("="*40)
        
        for level in [DataSharingLevel.PRIVATE, DataSharingLevel.ORGANIZATION, DataSharingLevel.PUBLIC]:
            count_total = db.query(Dataset).filter(
                Dataset.sharing_level == level,
                Dataset.is_deleted == False,
                Dataset.is_active == True
            ).count()
            
            count_shared = db.query(Dataset).filter(
                Dataset.sharing_level == level,
                Dataset.public_share_enabled == True,
                Dataset.is_deleted == False,
                Dataset.is_active == True
            ).count()
            
            print(f"{level.value:12}: {count_total} total, {count_shared} with sharing enabled")
        
    except Exception as e:
        print(f"Error during test: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_sharing_levels()