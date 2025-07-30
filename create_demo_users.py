#!/usr/bin/env python3
"""
Create Demo Users Script
Creates the 4 demo users across 2 organizations as specified in the summary:
- Demo Organization: demo1@demo.com/demo123, demo2@demo.com/demo123
- Open Source Community: opensource1@opensource.org/open123, opensource2@opensource.org/open123
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.core.auth import get_password_hash
from sqlalchemy.orm import Session

def create_demo_users():
    """Create demo users and organizations"""
    db = next(get_db())
    
    try:
        # Create Demo Organization
        demo_org = db.query(Organization).filter(Organization.name == "Demo Organization").first()
        if not demo_org:
            demo_org = Organization(
                name="Demo Organization",
                slug="demo-organization",
                description="Demo organization for testing login functionality",
                is_active=True
            )
            db.add(demo_org)
            db.commit()
            db.refresh(demo_org)
            print("✅ Created Demo Organization")
        else:
            print("📋 Demo Organization already exists")
        
        # Create Open Source Community
        opensource_org = db.query(Organization).filter(Organization.name == "Open Source Community").first()
        if not opensource_org:
            opensource_org = Organization(
                name="Open Source Community",
                slug="open-source-community",
                description="Open source community for collaborative development",
                is_active=True
            )
            db.add(opensource_org)
            db.commit()
            db.refresh(opensource_org)
            print("✅ Created Open Source Community")
        else:
            print("📋 Open Source Community already exists")
        
        # Demo users data
        demo_users_data = [
            {
                "email": "demo1@demo.com",
                "password": "demo123",
                "full_name": "Demo User 1",
                "organization": demo_org,
                "role": "member"
            },
            {
                "email": "demo2@demo.com", 
                "password": "demo123",
                "full_name": "Demo User 2",
                "organization": demo_org,
                "role": "member"
            },
            {
                "email": "opensource1@opensource.org",
                "password": "open123",
                "full_name": "Open Source User 1",
                "organization": opensource_org,
                "role": "member"
            },
            {
                "email": "opensource2@opensource.org",
                "password": "open123", 
                "full_name": "Open Source User 2",
                "organization": opensource_org,
                "role": "member"
            }
        ]
        
        # Create demo users
        created_count = 0
        for user_data in demo_users_data:
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing_user:
                new_user = User(
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    is_active=True,
                    is_superuser=False,
                    organization_id=user_data["organization"].id,
                    role=user_data["role"]
                )
                db.add(new_user)
                created_count += 1
                print(f"✅ Created user: {user_data['email']} / {user_data['password']}")
            else:
                print(f"📋 User already exists: {user_data['email']}")
        
        if created_count > 0:
            db.commit()
            print(f"\n🎉 Successfully created {created_count} demo users!")
        else:
            print("\n📋 All demo users already exist")
        
        # Verify demo users
        print("\n📊 Demo Users Summary:")
        for user_data in demo_users_data:
            user = db.query(User).filter(User.email == user_data["email"]).first()
            if user:
                org_name = user.organization.name if user.organization else "No Organization"
                print(f"  ✅ {user.email} ({org_name})")
            else:
                print(f"  ❌ {user_data['email']} - NOT FOUND")
                
    except Exception as e:
        print(f"❌ Error creating demo users: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Creating Demo Users for Login Testing")
    print("=" * 50)
    create_demo_users()