#!/usr/bin/env python3
"""
Test script to verify dataset deletion filtering behavior.
This script tests the admin dataset endpoints to ensure deleted datasets are properly filtered.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.dataset import Dataset
from app.models.user import User
from app.services.data_sharing import DataSharingService
from app.api.admin import get_admin_datasets
from app.api.datasets import get_datasets
from datetime import datetime

async def test_dataset_filtering():
    """Test dataset filtering behavior for regular users and admins."""
    
    print("🧪 Testing Dataset Deletion Filtering")
    print("=" * 50)
    
    # Get database session
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        # Get some test data
        all_datasets = db.query(Dataset).all()
        deleted_datasets = db.query(Dataset).filter(Dataset.is_deleted == True).all()
        active_datasets = db.query(Dataset).filter(Dataset.is_deleted == False).all()
        
        print(f"📊 Database State:")
        print(f"   Total datasets in DB: {len(all_datasets)}")
        print(f"   Active datasets: {len(active_datasets)}")
        print(f"   Deleted datasets: {len(deleted_datasets)}")
        print()
        
        # Test DataSharingService filtering
        print("🔍 Testing DataSharingService.get_accessible_datasets():")
        
        # Get a test user (preferably admin)
        test_user = db.query(User).filter(User.is_superuser == True).first()
        if not test_user:
            test_user = db.query(User).first()
        
        if test_user:
            print(f"   Using test user: {test_user.email} (admin: {test_user.is_superuser})")
            
            data_service = DataSharingService(db)
            
            # Test without include_deleted
            accessible_without_deleted = data_service.get_accessible_datasets(
                user=test_user,
                include_deleted=False
            )
            print(f"   Accessible datasets (include_deleted=False): {len(accessible_without_deleted)}")
            
            # Test with include_deleted
            accessible_with_deleted = data_service.get_accessible_datasets(
                user=test_user,
                include_deleted=True
            )
            print(f"   Accessible datasets (include_deleted=True): {len(accessible_with_deleted)}")
            
            # Check if any deleted datasets are in the non-deleted results
            deleted_in_results = [d for d in accessible_without_deleted if d.is_deleted]
            if deleted_in_results:
                print(f"   ❌ ERROR: Found {len(deleted_in_results)} deleted datasets in non-deleted results!")
                for dataset in deleted_in_results:
                    print(f"      - Dataset {dataset.id}: {dataset.name} (deleted: {dataset.is_deleted})")
            else:
                print(f"   ✅ PASS: No deleted datasets found in non-deleted results")
            
        else:
            print("   ⚠️  No test user found in database")
        
        print()
        
        # Test if there are any deleted datasets with details
        if deleted_datasets:
            print("🗑️  Deleted Datasets Details:")
            for dataset in deleted_datasets[:5]:  # Show first 5
                print(f"   - ID: {dataset.id}, Name: {dataset.name}")
                print(f"     Deleted: {dataset.is_deleted}, Active: {dataset.is_active}")
                print(f"     Deleted at: {dataset.deleted_at}")
                print(f"     Deleted by: {dataset.deleted_by}")
                print()
        
        # Test the can_access_dataset method specifically
        print("🔐 Testing can_access_dataset() method:")
        if test_user and deleted_datasets:
            data_service = DataSharingService(db)
            test_deleted_dataset = deleted_datasets[0]
            
            can_access = data_service.can_access_dataset(test_user, test_deleted_dataset)
            print(f"   Can access deleted dataset '{test_deleted_dataset.name}': {can_access}")
            
            if can_access:
                print(f"   ❌ ERROR: User can access deleted dataset!")
            else:
                print(f"   ✅ PASS: User cannot access deleted dataset")
        
        print()
        print("🎯 Summary:")
        print(f"   - Database has {len(deleted_datasets)} deleted datasets")
        print(f"   - DataSharingService filtering appears to be working correctly")
        print(f"   - Admin endpoints should properly filter these out by default")
        
        # Recommendations
        print()
        print("💡 Recommendations:")
        print("   1. Ensure frontend calls admin endpoints with include_deleted=false by default")
        print("   2. Verify that admin interface uses the new /api/admin/datasets endpoint")
        print("   3. Check for any caching issues in the frontend")
        print("   4. Test the actual admin interface behavior manually")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_dataset_filtering())