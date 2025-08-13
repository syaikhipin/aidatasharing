#!/usr/bin/env python3
"""
Test Simulation Data Script
Quick verification of the comprehensive simulation data for manual testing.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import get_db
from app.models.dataset import Dataset, DatasetType, DatasetStatus, DataSharingLevel
from app.models.user import User
from app.models.organization import Organization

def test_simulation_data():
    """Test and display the simulation data."""
    print("🧪 Testing Comprehensive Simulation Data")
    print("=" * 50)
    
    db = next(get_db())
    
    try:
        # Test organizations
        print("\n🏢 Organizations:")
        organizations = db.query(Organization).all()
        for org in organizations:
            user_count = db.query(User).filter(User.organization_id == org.id).count()
            dataset_count = db.query(Dataset).filter(Dataset.organization_id == org.id).count()
            print(f"  📋 {org.name}")
            print(f"      Slug: {org.slug}")
            print(f"      Users: {user_count}")
            print(f"      Datasets: {dataset_count}")
            print(f"      Active: {org.is_active}")
        
        # Test users by organization
        print(f"\n👥 Users by Organization:")
        for org in organizations:
            users = db.query(User).filter(User.organization_id == org.id).all()
            if users:
                print(f"\n  🏢 {org.name}:")
                for user in users:
                    datasets_owned = db.query(Dataset).filter(Dataset.owner_id == user.id).count()
                    print(f"    👤 {user.email}")
                    print(f"        Name: {user.full_name}")
                    print(f"        Role: {user.role}")
                    print(f"        Datasets Owned: {datasets_owned}")
                    print(f"        Active: {user.is_active}")
        
        # Test datasets by type and sharing level
        print(f"\n📊 Datasets Analysis:")
        
        # Web connector datasets
        web_datasets = db.query(Dataset).filter(
            (Dataset.connector_id.isnot(None)) | (Dataset.source_url.isnot(None))
        ).all()
        print(f"\n  🌐 Web Connector Datasets ({len(web_datasets)}):")
        for dataset in web_datasets:
            owner = db.query(User).filter(User.id == dataset.owner_id).first()
            print(f"    📡 {dataset.name} (ID: {dataset.id})")
            print(f"        Owner: {owner.email if owner else 'Unknown'}")
            print(f"        Sharing: {dataset.sharing_level.value}")
            print(f"        Source: {dataset.source_url}")
            print(f"        Connector: {dataset.connector_id}")
            print(f"        Rows: {dataset.row_count}")
        
        # Uploaded datasets
        uploaded_datasets = db.query(Dataset).filter(
            (Dataset.connector_id.is_(None)) & (Dataset.source_url.is_(None))
        ).all()
        print(f"\n  📁 Uploaded Datasets ({len(uploaded_datasets)}):")
        for dataset in uploaded_datasets:
            owner = db.query(User).filter(User.id == dataset.owner_id).first()
            print(f"    📊 {dataset.name} (ID: {dataset.id})")
            print(f"        Owner: {owner.email if owner else 'Unknown'}")
            print(f"        Sharing: {dataset.sharing_level.value}")
            print(f"        Type: {dataset.type.value}")
            print(f"        Rows: {dataset.row_count:,}")
            print(f"        Size: {dataset.size_bytes:,} bytes")
        
        # Sharing level statistics
        print(f"\n🔒 Sharing Level Statistics:")
        all_datasets = db.query(Dataset).all()
        sharing_stats = {}
        for dataset in all_datasets:
            level = dataset.sharing_level.value
            sharing_stats[level] = sharing_stats.get(level, 0) + 1
        
        for level, count in sharing_stats.items():
            print(f"  📋 {level.title()}: {count} datasets")
        
        # Test credentials summary
        print(f"\n🔑 Test Credentials Summary:")
        all_users = db.query(User).all()
        for user in all_users:
            org = db.query(Organization).filter(Organization.id == user.organization_id).first()
            # Determine password based on email domain
            password = "tech2024" if "techcorp" in user.email else \
                      "data2024" if "datasci" in user.email else \
                      "startup2024" if "startuplab" in user.email else \
                      "research2024" if "research" in user.email else "demo123"
            print(f"  👤 {user.email} / {password}")
            print(f"      Organization: {org.name if org else 'Unknown'}")
            print(f"      Role: {user.role}")
        
        # Manual testing scenarios
        print(f"\n🧪 Manual Testing Scenarios:")
        print(f"  1. Cross-Organization Access:")
        print(f"     - Login as alice.smith@techcorp.com")
        print(f"     - Try to access datasets from other organizations")
        print(f"     - Verify sharing level restrictions")
        
        print(f"\n  2. Dataset Type Testing:")
        print(f"     - Test web connector datasets (real-time data)")
        print(f"     - Test uploaded datasets (static data)")
        print(f"     - Verify AI chat context differences")
        
        print(f"\n  3. Sharing Level Testing:")
        print(f"     - PUBLIC: Should be visible to all users")
        print(f"     - ORGANIZATION: Only visible within same org")
        print(f"     - PRIVATE: Only visible to owner")
        
        print(f"\n  4. Proxy Service Testing:")
        print(f"     - Test different database connectors")
        print(f"     - Verify proxy port connectivity (10101-10107)")
        print(f"     - Test MindsDB integration")
        
        print(f"\n  5. Role-Based Testing:")
        print(f"     - Admin users: Full access within organization")
        print(f"     - Regular users: Limited access based on sharing")
        print(f"     - Cross-role data sharing verification")
        
        print(f"\n✅ Simulation Data Test Complete!")
        print(f"   🏢 Organizations: {len(organizations)}")
        print(f"   👥 Users: {len(all_users)}")
        print(f"   🌐 Web Connectors: {len(web_datasets)}")
        print(f"   📁 Uploaded Files: {len(uploaded_datasets)}")
        print(f"   📊 Total Datasets: {len(all_datasets)}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_simulation_data()