#!/usr/bin/env python3
"""
Clean up database: Delete all datasets and connectors, keep only Alice and Bob users
"""

import os
import sys
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Add backend directory to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from app.core.database import engine
from app.models.dataset import Dataset, DatabaseConnector
from app.models.user import User
from app.models.organization import Organization

# Create session
Session = sessionmaker(bind=engine)

def cleanup_database():
    """Clean up database keeping only Alice and Bob users"""
    session = Session()
    
    try:
        print("🧹 Starting database cleanup...\n")
        
        # 1. Delete all datasets
        print("📊 Deleting all datasets...")
        datasets_count = session.query(Dataset).count()
        session.query(Dataset).delete()
        print(f"   Deleted {datasets_count} datasets")
        
        # 2. Delete all database connectors
        print("🔌 Deleting all database connectors...")
        connectors_count = session.query(DatabaseConnector).count()
        session.query(DatabaseConnector).delete()
        print(f"   Deleted {connectors_count} connectors")
        
        # 3. Find Alice and Bob users
        print("\n👥 Finding Alice and Bob users...")
        alice = session.query(User).filter(User.email.ilike('%alice%')).first()
        bob = session.query(User).filter(User.email.ilike('%bob%')).first()
        
        if alice:
            print(f"   Found Alice: {alice.email} (ID: {alice.id})")
        if bob:
            print(f"   Found Bob: {bob.email} (ID: {bob.id})")
        
        # Get their organization IDs
        keep_org_ids = set()
        if alice and alice.organization_id:
            keep_org_ids.add(alice.organization_id)
            print(f"   Keeping Alice's organization (ID: {alice.organization_id})")
        if bob and bob.organization_id:
            keep_org_ids.add(bob.organization_id)
            print(f"   Keeping Bob's organization (ID: {bob.organization_id})")
        
        # 4. Delete other users (keeping Alice and Bob)
        print("\n🗑️ Deleting other users...")
        keep_user_ids = []
        if alice:
            keep_user_ids.append(alice.id)
        if bob:
            keep_user_ids.append(bob.id)
        
        if keep_user_ids:
            other_users = session.query(User).filter(~User.id.in_(keep_user_ids)).all()
            print(f"   Found {len(other_users)} users to delete:")
            for user in other_users:
                print(f"     - {user.email} (ID: {user.id})")
            
            # Delete other users
            session.query(User).filter(~User.id.in_(keep_user_ids)).delete()
            print(f"   Deleted {len(other_users)} users")
        else:
            print("   No users to keep found!")
        
        # 5. Delete other organizations
        print("\n🏢 Deleting other organizations...")
        if keep_org_ids:
            other_orgs = session.query(Organization).filter(~Organization.id.in_(keep_org_ids)).all()
            print(f"   Found {len(other_orgs)} organizations to delete:")
            for org in other_orgs:
                print(f"     - {org.name} (ID: {org.id})")
            
            # Delete other organizations
            session.query(Organization).filter(~Organization.id.in_(keep_org_ids)).delete()
            print(f"   Deleted {len(other_orgs)} organizations")
        else:
            print("   No organizations to keep!")
        
        # Commit all changes
        session.commit()
        print("\n✅ Database cleanup completed successfully!")
        
        # Show final state
        print("\n📋 Final database state:")
        remaining_users = session.query(User).all()
        remaining_orgs = session.query(Organization).all()
        remaining_datasets = session.query(Dataset).count()
        remaining_connectors = session.query(DatabaseConnector).count()
        
        print(f"   Users: {len(remaining_users)}")
        for user in remaining_users:
            print(f"     - {user.email} (ID: {user.id})")
        
        print(f"   Organizations: {len(remaining_orgs)}")
        for org in remaining_orgs:
            print(f"     - {org.name} (ID: {org.id})")
        
        print(f"   Datasets: {remaining_datasets}")
        print(f"   Connectors: {remaining_connectors}")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("🧹 DATABASE CLEANUP UTILITY")
    print("="*50)
    print("This will:")
    print("1. Delete ALL datasets")
    print("2. Delete ALL database connectors") 
    print("3. Keep only Alice and Bob users")
    print("4. Keep only Alice and Bob's organizations")
    print("5. Delete all other users and organizations")
    print("="*50)
    
    response = input("\nAre you sure you want to proceed? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        cleanup_database()
        print("\n🎉 Cleanup completed! You can now test manually with a clean state.")
    else:
        print("❌ Cleanup cancelled.")