#!/usr/bin/env python3
"""
Debug Demo Users Script
Test the demo users query directly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization

def debug_demo_users():
    """Debug demo users query"""
    db = next(get_db())
    
    try:
        print("🔍 Debugging Demo Users Query")
        print("=" * 50)
        
        # Get all users
        users = db.query(User).filter(User.is_active == True).all()
        print(f"Found {len(users)} active users:")
        
        for user in users:
            organization_name = "None"
            if user.organization_id:
                organization = db.query(Organization).filter(Organization.id == user.organization_id).first()
                if organization:
                    organization_name = organization.name
            
            print(f"  📧 {user.email}")
            print(f"     Name: {user.full_name}")
            print(f"     Org ID: {user.organization_id}")
            print(f"     Org Name: {organization_name}")
            print(f"     Active: {user.is_active}")
            print(f"     Superuser: {user.is_superuser}")
            print()
        
        # Test the demo password logic
        print("🧪 Testing Demo Password Logic:")
        print("=" * 50)
        
        demo_users = []
        for user in users:
            organization_name = None
            if user.organization_id:
                organization = db.query(Organization).filter(Organization.id == user.organization_id).first()
                if organization:
                    organization_name = organization.name
            
            demo_password = None
            description = ""
            
            # Demo Organization users
            if user.email == "demo1@demo.com":
                demo_password = "demo123"
                description = "Demo Organization Member 1"
            elif user.email == "demo2@demo.com":
                demo_password = "demo123"
                description = "Demo Organization Member 2"
            # Open Source Community users
            elif user.email == "opensource1@opensource.org":
                demo_password = "open123"
                description = "Open Source Community Member 1"
            elif user.email == "opensource2@opensource.org":
                demo_password = "open123"
                description = "Open Source Community Member 2"
            # Admin user
            elif user.email == "admin@example.com":
                demo_password = "admin123"
                description = "System Administrator with full access"
            elif user.is_superuser:
                demo_password = "admin123"
                description = "Administrator Account"
            
            if demo_password:
                demo_user = {
                    "email": user.email,
                    "password": demo_password,
                    "role": user.role or ("admin" if user.is_superuser else "member"),
                    "description": description,
                    "organization": organization_name,
                    "full_name": user.full_name,
                    "is_superuser": user.is_superuser
                }
                demo_users.append(demo_user)
                print(f"✅ Added demo user: {user.email}")
            else:
                print(f"❌ Skipped user: {user.email} (no demo password)")
        
        print(f"\n📊 Final Result: {len(demo_users)} demo users")
        for demo_user in demo_users:
            print(f"  {demo_user['email']} / {demo_user['password']} ({demo_user['organization']})")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_demo_users()