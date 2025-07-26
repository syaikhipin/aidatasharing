#!/usr/bin/env python3
"""
Test script to verify the data-access API functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.dataset import Dataset
from app.api.data_access import get_accessible_datasets
from app.core.auth import get_current_user
from fastapi import Depends

def test_data_access_api():
    db = SessionLocal()
    
    try:
        # Test with different users
        users = db.query(User).all()
        
        print("=== TESTING DATA ACCESS API ===")
        
        for user in users[:3]:  # Test with first 3 users
            print(f"\n🔍 Testing with User {user.id}: {user.email} (Org: {user.organization_id})")
            
            # Simulate the data access API call
            # Get datasets that are NOT owned by current user and NOT deleted
            query = db.query(Dataset).filter(
                Dataset.owner_id != user.id,  # Not owned by current user
                Dataset.is_deleted == False  # Not deleted
            )
            
            datasets = query.all()
            
            accessible_datasets = []
            for dataset in datasets:
                # Determine access status based on sharing level and organization
                has_access = False
                can_request = False
                
                sharing_level_str = dataset.sharing_level.value if hasattr(dataset.sharing_level, 'value') else str(dataset.sharing_level)
                sharing_level_str = sharing_level_str.upper()  # Normalize to uppercase
                
                print(f"    Checking dataset '{dataset.name}': sharing={sharing_level_str}, owner_org={dataset.organization_id}, user_org={user.organization_id}")
                
                if sharing_level_str == "PUBLIC":
                    has_access = True
                elif sharing_level_str == "ORGANIZATION" and dataset.organization_id == user.organization_id:
                    has_access = True
                elif sharing_level_str == "PRIVATE":
                    can_request = True
                
                # Only include datasets that user can either access or request access to
                if has_access or can_request:
                    accessible_datasets.append({
                        'name': dataset.name,
                        'owner_id': dataset.owner_id,
                        'organization_id': dataset.organization_id,
                        'sharing_level': sharing_level_str,
                        'has_access': has_access,
                        'can_request': can_request
                    })
            
            print(f"  📊 Found {len(accessible_datasets)} accessible datasets:")
            for ds in accessible_datasets:
                access_type = "✅ Can Access" if ds['has_access'] else "🔑 Can Request"
                print(f"    {access_type}: {ds['name']} ({ds['sharing_level']}) from Org {ds['organization_id']}")
        
    except Exception as e:
        print(f"❌ Error testing data access API: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Testing data-access API functionality...")
    test_data_access_api()