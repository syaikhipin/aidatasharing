from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.auth import get_password_hash
from app.models.user import User
from app.core.database import Base
from app.models.config import Configuration
from app.models.organization import Organization, Department, OrganizationType
from app.models.dataset import (
    Dataset, DatasetAccessLog, DatasetModel, DatasetDownload,
    DatasetChatSession, ChatMessage, DatasetShareAccess,
    DatabaseConnector, LLMConfiguration, ShareAccessSession
)
from app.models.analytics import (
    DatasetAccess, ChatInteraction, 
    APIUsage, UsageStats, SystemMetrics
)
from app.models.file_handler import FileUpload, MindsDBHandler, FileProcessingLog
from migrations.migration_manager import MigrationManager
import logging
import sys
import os
from pathlib import Path
import os

# Add database path for migration manager
# sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "database"))
# from migration_manager import MigrationManager

logger = logging.getLogger(__name__)


def init_db():
    """Initialize database with tables and default data."""
    # Create storage directory if it doesn't exist
    storage_dir = Path("./storage")
    storage_dir.mkdir(exist_ok=True)
    
    uploads_dir = storage_dir / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Run database migrations
    migration_manager = MigrationManager()
    migration_manager.migrate()
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create default organizations first
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
                if org_data["slug"] == "system-admin":
                    admin_org = org
            else:
                if org_data["slug"] == "system-admin":
                    admin_org = existing_org
        
        # Create superuser if it doesn't exist
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
            print(f"Superuser created: {settings.FIRST_SUPERUSER}")
        else:
            # Update existing admin to have organization if missing
            if not user.organization_id and admin_org:
                user.organization_id = admin_org.id
                user.role = "admin"
                print(f"Updated admin user with organization: {admin_org.name}")
            print(f"Superuser already exists: {settings.FIRST_SUPERUSER}")
        
        # Create permanent test user for testing purposes
        test_user_email = "testuser@demo.com"
        test_user = db.query(User).filter(User.email == test_user_email).first()
        if not test_user:
            # Get demo organization for test user
            demo_org = db.query(Organization).filter(Organization.slug == "demo-org").first()
            test_user = User(
                email=test_user_email,
                hashed_password=get_password_hash("testpassword123"),
                full_name="Test User",
                is_active=True,
                is_superuser=False,
                organization_id=demo_org.id if demo_org else None,
                role="member"
            )
            db.add(test_user)
            print(f"Test user created: {test_user_email}")
        else:
            print(f"Test user already exists: {test_user_email}")
        
        # Create default configurations
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
            }
        ]
        
        for config_data in default_configs:
            existing_config = db.query(Configuration).filter(
                Configuration.key == config_data["key"]
            ).first()
            
            if not existing_config:
                config = Configuration(**config_data)
                db.add(config)
        
        db.commit()
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()