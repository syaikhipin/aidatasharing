#!/usr/bin/env python3
"""
Database Schema Creation Script
Creates all tables in the correct order to handle foreign key dependencies.
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.auth import get_password_hash
import logging

# Import all models to ensure they are registered with SQLAlchemy
from app.models import *  # This will import all models and register them
from app.core.database import Base

logger = logging.getLogger(__name__)


def create_database_schema():
    """Create all database tables with proper dependencies."""
    print("🔧 Creating database schema...")
    
    # Create engine
    engine = create_engine(
        settings.DATABASE_URL,
        # Use configuration from .env file
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
        pool_recycle=settings.DB_POOL_RECYCLE,
        connect_args={
            "connect_timeout": settings.DB_CONNECTION_TIMEOUT,
        } if "postgresql" in settings.DATABASE_URL else {}
    )
    
    # Drop all tables first (for clean slate)
    print("📋 Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)
    
    # Create all tables
    print("🏗️  Creating all tables...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database schema created successfully!")
    return engine


def create_default_data(engine):
    """Create default organizations, users, and configurations."""
    print("📊 Creating default data...")
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create default organizations
        print("🏢 Creating default organizations...")
        default_orgs = [
            {
                "name": "System Administration",
                "slug": "system-admin",
                "description": "Default organization for system administrators",
                "type": OrganizationType.ENTERPRISE,
                "is_active": True
            },
            {
                "name": "Demo Organization",
                "slug": "demo-org",
                "description": "A demo organization for testing purposes",
                "type": OrganizationType.SMALL_BUSINESS,
                "is_active": True
            },
            {
                "name": "Open Source Community",
                "slug": "open-source",
                "description": "Community for open source projects",
                "type": OrganizationType.NONPROFIT,
                "is_active": True
            }
        ]
        
        admin_org = None
        for org_data in default_orgs:
            existing_org = db.query(Organization).filter(
                Organization.slug == org_data["slug"]
            ).first()
            
            if not existing_org:
                org = Organization(**org_data)
                db.add(org)
                db.flush()  # Get the ID
                print(f"   ✅ Created organization: {org.name}")
                if org_data["slug"] == "system-admin":
                    admin_org = org
            else:
                print(f"   ⚠️  Organization already exists: {existing_org.name}")
                if org_data["slug"] == "system-admin":
                    admin_org = existing_org
        
        # Create superuser
        print("👤 Creating superuser...")
        user = db.query(User).filter(User.email == settings.FIRST_SUPERUSER).first()
        if not user:
            user = User(
                email=settings.FIRST_SUPERUSER,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                full_name="Super Admin",
                is_active=True,
                is_superuser=True,
                organization_id=admin_org.id if admin_org else None,
                role="admin"
            )
            db.add(user)
            print(f"   ✅ Created superuser: {settings.FIRST_SUPERUSER}")
        else:
            # Update existing admin to have organization if missing
            if not user.organization_id and admin_org:
                user.organization_id = admin_org.id
                user.role = "admin"
                print(f"   🔄 Updated admin user with organization: {admin_org.name}")
            print(f"   ⚠️  Superuser already exists: {settings.FIRST_SUPERUSER}")
        
        # Create test users - 2 users per organization (4 total)
        print("🧪 Creating test users...")
        demo_org = db.query(Organization).filter(Organization.slug == "demo-org").first()
        opensource_org = db.query(Organization).filter(Organization.slug == "open-source").first()
        
        test_users = [
            # Demo Organization Users
            {
                "email": "demo1@demo.com",
                "password": "demo123",
                "full_name": "Demo User 1",
                "organization_id": demo_org.id if demo_org else None,
                "role": "admin",
                "is_superuser": False
            },
            {
                "email": "demo2@demo.com", 
                "password": "demo123",
                "full_name": "Demo User 2",
                "organization_id": demo_org.id if demo_org else None,
                "role": "member",
                "is_superuser": False
            },
            # Open Source Organization Users
            {
                "email": "opensource1@opensource.org",
                "password": "open123",
                "full_name": "Open Source User 1",
                "organization_id": opensource_org.id if opensource_org else None,
                "role": "owner",
                "is_superuser": False
            },
            {
                "email": "opensource2@opensource.org",
                "password": "open123",
                "full_name": "Open Source User 2",
                "organization_id": opensource_org.id if opensource_org else None,
                "role": "member",
                "is_superuser": False
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
                    is_superuser=user_data["is_superuser"],
                    organization_id=user_data["organization_id"],
                    role=user_data["role"]
                )
                db.add(test_user)
                print(f"   ✅ Created test user: {user_data['email']} ({user_data['full_name']})")
            else:
                print(f"   ⚠️  Test user already exists: {existing_user.email}")
        
        # Create default configurations
        print("⚙️  Creating default configurations...")
        default_configs = [
            {
                "key": "google_api_key",
                "value": None,
                "description": "Google API key for Gemini Flash integration"
            },
            {
                "key": "mindsdb_url", 
                "value": settings.MINDSDB_URL,
                "description": "MindsDB server URL"
            },
            {
                "key": "default_sharing_level",
                "value": "ORGANIZATION",
                "description": "Default sharing level for new datasets"
            },
            {
                "key": "max_file_size_mb",
                "value": "100",
                "description": "Maximum file size for uploads in MB"
            }
        ]
        
        for config_data in default_configs:
            existing_config = db.query(Configuration).filter(
                Configuration.key == config_data["key"]
            ).first()
            
            if not existing_config:
                config = Configuration(**config_data)
                db.add(config)
                print(f"   ✅ Created configuration: {config.key}")
            else:
                print(f"   ⚠️  Configuration already exists: {existing_config.key}")
        
        db.commit()
        print("✅ Default data created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating default data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """Main function to create schema and default data."""
    try:
        # Create schema
        engine = create_database_schema()
        
        # Create default data
        create_default_data(engine)
        
        print("\n🎉 Database initialization completed successfully!")
        print("📝 Summary:")
        print("   - All tables created")
        print("   - Default organizations created")
        print("   - Superuser created")
        print("   - Default configurations created")
        print("\n🚀 You can now start the application!")
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        raise


if __name__ == "__main__":
    main() 