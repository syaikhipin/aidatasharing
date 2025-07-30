#!/usr/bin/env python3
"""
Create a test user for testing the sharing functionality
"""

import sys
import os
sys.path.insert(0, './backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.auth import get_password_hash
from app.models.user import User
from app.models.organization import Organization

def create_test_user():
    """Create a test user in the Demo Organization."""
    print("🧪 Creating test user...")
    
    # Create engine
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    )
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get Demo Organization
        demo_org = db.query(Organization).filter(
            Organization.slug == "demo-org"
        ).first()
        
        if not demo_org:
            print("❌ Demo Organization not found!")
            return False
        
        # Check if test user already exists
        test_email = "test@demo.com"
        existing_user = db.query(User).filter(User.email == test_email).first()
        
        if existing_user:
            print(f"⚠️  Test user already exists: {test_email}")
            # Update to ensure they're in the demo org
            if not existing_user.organization_id:
                existing_user.organization_id = demo_org.id
                existing_user.role = "member"
                db.commit()
                print(f"   🔄 Updated user to belong to: {demo_org.name}")
            return True
        
        # Create test user
        test_user = User(
            email=test_email,
            hashed_password=get_password_hash("password123"),
            full_name="Test User",
            is_active=True,
            is_superuser=False,
            organization_id=demo_org.id,
            role="member"
        )
        
        db.add(test_user)
        db.commit()
        
        print(f"✅ Created test user: {test_email}")
        print(f"   Organization: {demo_org.name}")
        print(f"   Password: password123")
        print(f"   Role: member")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def list_users():
    """List all users and their organizations."""
    print("\n📋 Current users:")
    
    # Create engine
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    )
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        users = db.query(User).all()
        for user in users:
            org_name = "No Organization"
            if user.organization:
                org_name = user.organization.name
            
            print(f"   📧 {user.email} - {org_name} ({user.role})")
            
    except Exception as e:
        print(f"❌ Error listing users: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
    list_users()