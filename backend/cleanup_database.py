#!/usr/bin/env python3
"""
Database Cleanup Script
Cleans up datasets and related data while preserving users.
Sets up default organizations with Alice and Bob, and keeps admin user.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseCleaner:
    def __init__(self, db_path=None):
        if db_path is None:
            backend_dir = Path(__file__).parent
            root_dir = backend_dir.parent
            db_path = root_dir / "storage" / "aishare_platform.db"
        
        self.db_path = db_path
        logger.info(f"Using database at: {self.db_path}")
    
    def backup_database(self):
        """Create a backup of the database before cleaning"""
        backup_path = self.db_path.parent / f"aishare_platform_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"✅ Database backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"❌ Failed to backup database: {e}")
            return None
    
    def clean_datasets(self, conn):
        """Clean up all dataset-related tables"""
        cursor = conn.cursor()
        
        # Tables to clean (order matters due to foreign key constraints)
        dataset_tables = [
            "chat_messages",
            "dataset_chat_sessions",
            "dataset_share_accesses",
            "share_access_sessions",
            "dataset_access_logs",
            "dataset_downloads",
            "dataset_files",
            "dataset_models",
            "dataset_access",
            "file_uploads",
            "file_processing_logs",
            "datasets",
            "database_connectors",
            "proxy_connectors",
            "proxy_access_logs",
            "proxy_credential_vault",
            "shared_proxy_links"
        ]
        
        for table in dataset_tables:
            try:
                cursor.execute(f"DELETE FROM {table}")
                count = cursor.rowcount
                if count > 0:
                    logger.info(f"  ✓ Cleared {count} rows from {table}")
            except sqlite3.OperationalError as e:
                if "no such table" in str(e):
                    logger.warning(f"  ⚠ Table {table} does not exist, skipping")
                else:
                    logger.error(f"  ✗ Error cleaning {table}: {e}")
    
    def setup_default_organizations(self, conn):
        """Set up two default organizations with Alice and Bob"""
        cursor = conn.cursor()
        
        # First, check existing organizations
        cursor.execute("SELECT id, name, slug FROM organizations")
        existing_orgs = cursor.fetchall()
        logger.info(f"Found {len(existing_orgs)} existing organizations")
        
        # Clear existing organizations (except the default ones we'll create)
        cursor.execute("DELETE FROM organizations")
        logger.info("Cleared existing organizations")
        
        # Create two default organizations
        organizations = [
            {
                "name": "Alice's Organization",
                "slug": "alice-org",
                "description": "Default organization for Alice and her team",
                "type": "enterprise",
                "is_active": True,
                "allow_external_sharing": True,
                "default_sharing_level": "organization",
                "contact_email": "alice@example.com"
            },
            {
                "name": "Bob's Organization", 
                "slug": "bob-org",
                "description": "Default organization for Bob and his team",
                "type": "enterprise",
                "is_active": True,
                "allow_external_sharing": True,
                "default_sharing_level": "organization",
                "contact_email": "bob@example.com"
            }
        ]
        
        org_ids = {}
        for org in organizations:
            cursor.execute("""
                INSERT INTO organizations (
                    name, slug, description, type, is_active,
                    allow_external_sharing, default_sharing_level,
                    contact_email, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                org["name"], org["slug"], org["description"], 
                org["type"], org["is_active"], org["allow_external_sharing"],
                org["default_sharing_level"], org["contact_email"]
            ))
            org_ids[org["slug"]] = cursor.lastrowid
            logger.info(f"  ✓ Created organization: {org['name']} (ID: {cursor.lastrowid})")
        
        return org_ids
    
    def ensure_default_users(self, conn, org_ids):
        """Ensure Alice, Bob, and Admin users exist with proper setup"""
        cursor = conn.cursor()
        
        # Define default users
        default_users = [
            {
                "email": "alice@example.com",
                "full_name": "Alice",
                "organization_id": org_ids.get("alice-org"),
                "role": "owner",
                "is_superuser": False
            },
            {
                "email": "bob@example.com",
                "full_name": "Bob",
                "organization_id": org_ids.get("bob-org"),
                "role": "owner",
                "is_superuser": False
            },
            {
                "email": "admin@example.com",
                "full_name": "Admin",
                "organization_id": org_ids.get("alice-org"),  # Admin belongs to Alice's org by default
                "role": "admin",
                "is_superuser": True
            }
        ]
        
        for user_data in default_users:
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (user_data["email"],))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # Update existing user
                cursor.execute("""
                    UPDATE users 
                    SET organization_id = ?, role = ?, is_superuser = ?, updated_at = datetime('now')
                    WHERE email = ?
                """, (user_data["organization_id"], user_data["role"], 
                     user_data["is_superuser"], user_data["email"]))
                logger.info(f"  ✓ Updated existing user: {user_data['full_name']} ({user_data['email']})")
            else:
                # Create new user with default password (should be changed on first login)
                cursor.execute("""
                    INSERT INTO users (
                        email, full_name, hashed_password, organization_id, 
                        role, is_active, is_superuser, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """, (
                    user_data["email"], user_data["full_name"],
                    "$2b$12$defaultPasswordHash",  # This should be changed
                    user_data["organization_id"], user_data["role"],
                    True, user_data["is_superuser"]
                ))
                logger.info(f"  ✓ Created default user: {user_data['full_name']} ({user_data['email']})")
    
    def assign_users_to_organizations(self, conn, org_ids):
        """Assign existing users to organizations"""
        cursor = conn.cursor()
        
        # Get all users (excluding the ones we already handled)
        cursor.execute("""
            SELECT id, email, full_name 
            FROM users 
            WHERE email NOT IN ('alice@example.com', 'bob@example.com', 'admin@example.com')
        """)
        users = cursor.fetchall()
        logger.info(f"Found {len(users)} additional users to assign")
        
        # Assign users based on their email or name
        for user_id, email, full_name in users:
            org_id = None
            role = "member"  # default role
            
            # Determine organization based on email or name
            if email:
                email_lower = email.lower()
                if "alice" in email_lower:
                    org_id = org_ids.get("alice-org")
                elif "bob" in email_lower:
                    org_id = org_ids.get("bob-org") 
            
            # If no match by email, try by name
            if not org_id and full_name:
                name_lower = full_name.lower()
                if "alice" in name_lower:
                    org_id = org_ids.get("alice-org")
                elif "bob" in name_lower:
                    org_id = org_ids.get("bob-org")
            
            # Default to Alice's organization if no match
            if not org_id:
                org_id = org_ids.get("alice-org")
                role = "member"
            
            # Update user's organization
            cursor.execute("""
                UPDATE users 
                SET organization_id = ?, role = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (org_id, role, user_id))
            
            org_name = "Alice's Organization" if org_id == org_ids.get("alice-org") else "Bob's Organization"
            logger.info(f"  ✓ Assigned {full_name or email} to {org_name} as {role}")
    
    def reset_counters(self, conn):
        """Reset auto-increment counters for cleaned tables"""
        cursor = conn.cursor()
        
        # Reset sqlite_sequence for cleaned tables
        cursor.execute("""
            UPDATE sqlite_sequence 
            SET seq = 0 
            WHERE name IN (
                'datasets', 'dataset_files', 'dataset_access_logs',
                'dataset_share_accesses', 'file_uploads', 'database_connectors',
                'proxy_connectors', 'shared_proxy_links'
            )
        """)
        logger.info("Reset auto-increment counters")
    
    def show_summary(self, conn):
        """Show summary of the database after cleanup"""
        cursor = conn.cursor()
        
        print("\n" + "="*60)
        print("DATABASE SUMMARY AFTER CLEANUP")
        print("="*60)
        
        # Users summary
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"\n👥 Users: {user_count}")
        
        cursor.execute("""
            SELECT u.full_name, u.email, o.name as org_name, u.role, u.is_superuser
            FROM users u
            LEFT JOIN organizations o ON u.organization_id = o.id
            ORDER BY u.is_superuser DESC, o.name, u.role
        """)
        users = cursor.fetchall()
        for user in users:
            superuser_badge = " 🔑" if user[4] else ""
            print(f"   - {user[0] or 'Unknown'} ({user[1]}) - {user[2]} [{user[3]}]{superuser_badge}")
        
        # Organizations summary  
        cursor.execute("SELECT COUNT(*) FROM organizations")
        org_count = cursor.fetchone()[0]
        print(f"\n🏢 Organizations: {org_count}")
        
        cursor.execute("SELECT name, slug, type FROM organizations ORDER BY name")
        orgs = cursor.fetchall()
        for org in orgs:
            cursor.execute("""
                SELECT COUNT(*) FROM users WHERE organization_id = (
                    SELECT id FROM organizations WHERE slug = ?
                )
            """, (org[1],))
            member_count = cursor.fetchone()[0]
            print(f"   - {org[0]} ({org[1]}) - {org[2]} - {member_count} members")
        
        # Dataset tables summary
        print(f"\n📊 Dataset Tables (should be empty):")
        dataset_tables = ["datasets", "dataset_files", "dataset_share_accesses", "file_uploads"]
        for table in dataset_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                status = "✓ Empty" if count == 0 else f"⚠ {count} rows"
                print(f"   - {table}: {status}")
            except:
                print(f"   - {table}: ✗ Not found")
        
        print("\n" + "="*60)
    
    def run(self, skip_backup=False):
        """Run the complete cleanup process"""
        logger.info("Starting database cleanup...")
        
        # Create backup unless skipped
        if not skip_backup:
            backup_path = self.backup_database()
            if not backup_path:
                response = input("⚠️  Failed to create backup. Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    logger.info("Cleanup cancelled")
                    return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = OFF")  # Disable foreign key checks during cleanup
            
            # Step 1: Clean datasets
            logger.info("\n📊 Cleaning dataset-related tables...")
            self.clean_datasets(conn)
            
            # Step 2: Setup default organizations
            logger.info("\n🏢 Setting up default organizations...")
            org_ids = self.setup_default_organizations(conn)
            
            # Step 3: Ensure default users (Alice, Bob, Admin)
            logger.info("\n👤 Ensuring default users (Alice, Bob, Admin)...")
            self.ensure_default_users(conn, org_ids)
            
            # Step 4: Assign other users to organizations
            logger.info("\n👥 Assigning other users to organizations...")
            self.assign_users_to_organizations(conn, org_ids)
            
            # Step 5: Reset counters
            logger.info("\n🔄 Resetting counters...")
            self.reset_counters(conn)
            
            # Commit changes
            conn.commit()
            
            # Show summary
            self.show_summary(conn)
            
            conn.close()
            
            logger.info("\n✅ Database cleanup completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False

def main():
    """Main entry point"""
    import sys
    
    print("="*60)
    print("DATABASE CLEANUP UTILITY")
    print("="*60)
    print("\nThis will:")
    print("  1. Backup the current database")
    print("  2. Delete all datasets and related data")
    print("  3. Preserve all users")
    print("  4. Keep Admin user as superuser")
    print("  5. Create two default organizations (Alice's and Bob's)")
    print("  6. Assign users to organizations")
    print("\n⚠️  This operation cannot be undone (except by restoring backup)")
    
    response = input("\nDo you want to continue? (y/N): ")
    
    if response.lower() != 'y':
        print("Cleanup cancelled")
        sys.exit(0)
    
    cleaner = DatabaseCleaner()
    
    # Check for command line arguments
    skip_backup = "--skip-backup" in sys.argv
    
    if cleaner.run(skip_backup=skip_backup):
        print("\n✅ Cleanup completed! You can now:")
        print("  1. Restart the backend server")
        print("  2. Upload new datasets")
        print("  3. Create new share links")
        print("\nDefault users:")
        print("  - admin@example.com (Superuser)")
        print("  - alice@example.com (Owner of Alice's Organization)")
        print("  - bob@example.com (Owner of Bob's Organization)")
        sys.exit(0)
    else:
        print("\n❌ Cleanup failed! Check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()