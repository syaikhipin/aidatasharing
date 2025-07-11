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
from app.models.user import User
from app.core.database import Base
from app.models.organization import Organization, Department, OrganizationType, DataSharingLevel
from app.models.config import Configuration
from app.models.dataset import (
    Dataset, DatasetAccessLog, DatasetModel, DatasetChatSession, 
    ChatMessage, DatasetShareAccess, DatasetType, DatasetStatus, AIProcessingStatus
)
from app.models.file_handler import FileUpload, MindsDBHandler, FileProcessingLog
from app.models.analytics import (
    ActivityLog, UsageMetric, DatashareStats, UserSessionLog, 
    ModelPerformanceLog, ActivityType, UsageMetricType
)

logger = logging.getLogger(__name__)


def create_database_schema():
    """Create all database tables with proper dependencies."""
    print("🔧 Creating database schema...")
    
    # Create engine
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
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
        
        # Create default departments
        print("🏛️  Creating default departments...")
        if admin_org:
            default_departments = [
                {"name": "IT Administration", "description": "IT and system administration"},
                {"name": "Data Science", "description": "Data analysis and machine learning"},
                {"name": "Analytics", "description": "Business analytics and reporting"},
            ]
            
            for dept_data in default_departments:
                existing_dept = db.query(Department).filter(
                    Department.name == dept_data["name"],
                    Department.organization_id == admin_org.id
                ).first()
                
                if not existing_dept:
                    dept = Department(**dept_data, organization_id=admin_org.id)
                    db.add(dept)
                    print(f"   ✅ Created department: {dept.name}")
        
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
        print("   - Default departments created")
        print("   - Superuser created")
        print("   - Default configurations created")
        print("\n🚀 You can now start the application!")
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        raise


if __name__ == "__main__":
    main() 