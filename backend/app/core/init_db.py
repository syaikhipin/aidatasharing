from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.auth import get_password_hash
from app.models.user import User, Base
from app.models.config import Configuration
from app.models.organization import Organization, Department, OrganizationType
from app.models.dataset import (
    Dataset, DatasetAccessLog, DatasetModel,
    DatasetChatSession, ChatMessage, DatasetShareAccess
)
from app.models.file_handler import FileUpload, MindsDBHandler, FileProcessingLog
import logging
import sys
import os

# Add database path for migration manager
# sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "database"))
# from migration_manager import MigrationManager

logger = logging.getLogger(__name__)


def init_db():
    """Initialize database with tables and default data."""
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Run migrations using the migration manager
    # try:
    #     logger.info("Running database migrations...")
    #     migration_manager = MigrationManager()
    #     result = migration_manager.migrate()
        
    #     if result["status"] == "success":
    #         if result["executed"]:
    #             logger.info(f"Executed {len(result['executed'])} migrations: {result['executed']}")
    #         else:
    #             logger.info("All migrations are up to date")
    #     else:
    #         logger.warning(f"Migration partially failed: {result['message']}")
            
    # except Exception as e:
    #     logger.warning(f"Migration system failed: {e}")
    #     # Continue anyway as this is non-critical
    
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