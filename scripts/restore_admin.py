#!/usr/bin/env python3
"""
Restore admin user to the database
"""

import os
import sys
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime

# Add backend directory to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from app.core.database import engine
from app.models.user import User
from app.models.organization import Organization
from app.core.auth import get_password_hash

# Create session
Session = sessionmaker(bind=engine)

def restore_admin():
    """Restore admin user"""
    session = Session()
    
    try:
        print("👤 Restoring admin user...\n")
        
        # Check if admin already exists
        existing_admin = session.query(User).filter(User.email == "admin@example.com").first()
        if existing_admin:
            print(f"   Admin user already exists: {existing_admin.email} (ID: {existing_admin.id})")
            return
        
        # Find or create System Administration organization
        system_org = session.query(Organization).filter(Organization.name == "System Administration").first()
        if not system_org:
            print("🏢 Creating System Administration organization...")
            system_org = Organization(
                name="System Administration",
                slug="system-administration",  # Required slug field
                description="System administration and management organization",
                type="SMALL_BUSINESS",  # Use enum value
                is_active=True,
                allow_external_sharing=False,
                default_sharing_level="ORGANIZATION",  # Use enum value
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(system_org)
            session.commit()
            session.refresh(system_org)
            print(f"   Created organization: {system_org.name} (ID: {system_org.id})")
        else:
            print(f"🏢 Using existing organization: {system_org.name} (ID: {system_org.id})")
        
        # Create admin user
        print("👤 Creating admin user...")
        admin_user = User(
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),  # Default password
            full_name="System Administrator",
            is_active=True,
            is_superuser=True,
            organization_id=system_org.id,
            role="admin",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)
        
        print(f"✅ Admin user created successfully!")
        print(f"   Email: {admin_user.email}")
        print(f"   ID: {admin_user.id}")
        print(f"   Password: admin123")
        print(f"   Organization: {system_org.name}")
        print(f"   Role: {admin_user.role}")
        print(f"   Superuser: {admin_user.is_superuser}")
        
        # Show final user count
        print("\n📋 Current users in database:")
        all_users = session.query(User).all()
        for user in all_users:
            org_name = session.query(Organization).filter(Organization.id == user.organization_id).first()
            org_name = org_name.name if org_name else "No Organization"
            print(f"   - {user.email} ({user.role}) - {org_name}")
        
    except Exception as e:
        print(f"❌ Error restoring admin: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("👤 RESTORE ADMIN USER")
    print("="*30)
    restore_admin()
    print("\n🎉 Admin user restoration completed!")