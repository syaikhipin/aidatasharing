#!/usr/bin/env python3
"""
Simple script to create admin users for the AI Share Platform
"""
import sys
import os
sys.path.append('backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.user import User
from backend.app.models.organization import Organization, OrganizationType
from backend.app.core.auth import get_password_hash

# Database setup
DATABASE_URL = "sqlite:///./storage/aishare_platform.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_admin_users():
    """Create admin and test users"""
    db = SessionLocal()
    
    try:
        # Create default organization first
        admin_org = db.query(Organization).filter(Organization.slug == "system-admin").first()
        if not admin_org:
            admin_org = Organization(
                name="System Administration",
                slug="system-admin",
                description="Default organization for system administrators",
                type=OrganizationType.ENTERPRISE,
                is_active=True
            )
            db.add(admin_org)
            db.flush()
            print("✅ Created admin organization")
        
        # Create demo organization
        demo_org = db.query(Organization).filter(Organization.slug == "demo-org").first()
        if not demo_org:
            demo_org = Organization(
                name="Demo Organization",
                slug="demo-org",
                description="A demo organization for testing purposes",
                type=OrganizationType.SMALL_BUSINESS,
                is_active=True
            )
            db.add(demo_org)
            db.flush()
            print("✅ Created demo organization")
        
        # Create admin user
        admin_user = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin_user:
            admin_user = User(
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                full_name="Administrator",
                is_active=True,
                is_superuser=True,
                organization_id=admin_org.id,
                role="owner"
            )
            db.add(admin_user)
            print("✅ Created admin user: admin@example.com / admin123")
        else:
            print("ℹ️  Admin user already exists")
        
        # Create test users
        test_users = [
            {
                "email": "testuser@demo.com",
                "password": "testpassword123",
                "full_name": "Test User",
                "org": demo_org
            },
            {
                "email": "test@mailinator.com", 
                "password": "test123",
                "full_name": "Test User 2",
                "org": demo_org
            }
        ]
        
        for user_data in test_users:
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing_user:
                test_user = User(
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    is_active=True,
                    is_superuser=False,
                    organization_id=user_data["org"].id,
                    role="member"
                )
                db.add(test_user)
                print(f"✅ Created test user: {user_data['email']} / {user_data['password']}")
            else:
                print(f"ℹ️  Test user already exists: {user_data['email']}")
        
        db.commit()
        print("\n🎉 All users created successfully!")
        
        # List all users
        print("\n📋 Current users in database:")
        users = db.query(User).all()
        for user in users:
            print(f"   - {user.email} (Active: {user.is_active}, Admin: {user.is_superuser})")
        
    except Exception as e:
        print(f"❌ Error creating users: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Creating admin users for AI Share Platform...")
    create_admin_users()