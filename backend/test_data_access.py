#!/usr/bin/env python3
"""
Test script to create sample data for testing the data-access functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.dataset import Dataset, DatasetType, DatasetStatus
from app.models.organization import DataSharingLevel
from app.models.analytics import AccessRequest, RequestType, AccessLevel, RequestStatus, UrgencyLevel, RequestCategory
from datetime import datetime

def create_sample_data():
    db = SessionLocal()
    
    try:
        # Check if we already have organizations and users
        org_count = db.query(Organization).count()
        user_count = db.query(User).count()
        dataset_count = db.query(Dataset).count()
        
        print(f"📊 Current data: {org_count} organizations, {user_count} users, {dataset_count} datasets")
        
        # First, let's restore some deleted datasets and set up proper test data
        deleted_datasets = db.query(Dataset).filter(Dataset.is_deleted == True).all()
        if deleted_datasets:
            print(f"🔄 Found {len(deleted_datasets)} deleted datasets. Restoring some for testing...")
            
            # Restore a few datasets and assign them to different organizations
            for i, dataset in enumerate(deleted_datasets[:5]):
                dataset.is_deleted = False
                dataset.deleted_at = None
                dataset.deleted_by_id = None
                
                # Assign to different organizations for cross-org testing
                if i == 0:
                    dataset.organization_id = 2  # Demo Organization
                    dataset.owner_id = 6  # User in org 2
                    dataset.sharing_level = DataSharingLevel.PUBLIC
                elif i == 1:
                    dataset.organization_id = 3  # Open Source Community
                    dataset.owner_id = 7  # User in org 3 (if exists)
                    dataset.sharing_level = DataSharingLevel.ORGANIZATION
                elif i == 2:
                    dataset.organization_id = 4  # Default Organization
                    dataset.owner_id = 8  # User in org 4 (if exists)
                    dataset.sharing_level = DataSharingLevel.PRIVATE
                else:
                    dataset.organization_id = 2
                    dataset.sharing_level = DataSharingLevel.PUBLIC
                
                print(f"📝 Restored dataset '{dataset.name}' in org {dataset.organization_id} with {dataset.sharing_level} sharing")
        
        # Update existing active datasets to have different sharing levels for testing
        active_datasets = db.query(Dataset).filter(Dataset.is_deleted == False).all()
        sharing_levels = [DataSharingLevel.PUBLIC, DataSharingLevel.ORGANIZATION, DataSharingLevel.PRIVATE]
        
        for i, dataset in enumerate(active_datasets):
            new_level = sharing_levels[i % len(sharing_levels)]
            if dataset.sharing_level != new_level:
                dataset.sharing_level = new_level
                print(f"📝 Updated dataset '{dataset.name}' sharing level to {new_level}")
        
        db.commit()
        
        # Show final state
        print("\n=== FINAL TEST DATA STATE ===")
        active_datasets = db.query(Dataset).filter(Dataset.is_deleted == False).all()
        for dataset in active_datasets:
            print(f"Dataset: {dataset.name}")
            print(f"  Owner: {dataset.owner_id} (Org: {dataset.organization_id})")
            print(f"  Sharing: {dataset.sharing_level}")
            print(f"  Deleted: {dataset.is_deleted}")
            print()
        
        # Check access requests
        request_count = db.query(AccessRequest).count()
        print(f"📋 Current access requests: {request_count}")
        
        print("✅ Sample data setup complete!")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Setting up sample data for data-access testing...")
    create_sample_data()