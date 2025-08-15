#!/usr/bin/env python3
"""
Test Database Cleanup Functionality

This script demonstrates the database cleanup functionality by:
1. Showing current cleanup statistics
2. Optionally running cleanup operations
3. Verifying the results

Usage:
    python test_database_cleanup.py [--run-cleanup] [--force]
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime

# Add the backend directory to the Python path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.database import Base
from app.models.user import User
from app.models.organization import Organization
from app.models.dataset import Dataset

# Database configuration
DATABASE_URL = "sqlite:///storage/aishare_platform.db"

class CleanupTester:
    def __init__(self, database_url: str = DATABASE_URL):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_database_overview(self) -> dict:
        """Get a comprehensive overview of the database state"""
        with self.SessionLocal() as session:
            # Basic counts
            stats = {
                'users': session.query(User).count(),
                'organizations': session.query(Organization).count(),
                'datasets': session.query(Dataset).count(),
                'active_datasets': session.query(Dataset).filter(
                    Dataset.is_active == True, 
                    Dataset.is_deleted == False
                ).count(),
            }
            
            # Find orphaned datasets
            orphaned_datasets = session.query(Dataset).filter(
                ~Dataset.owner_id.in_(session.query(User.id))
            ).all()
            
            # Find empty organizations (excluding admin)
            empty_orgs_query = session.query(Organization).filter(
                ~Organization.id.in_(
                    session.query(User.organization_id).filter(User.organization_id.isnot(None))
                )
            )
            
            empty_orgs = []
            for org in empty_orgs_query.all():
                if not any(keyword in org.name.lower() for keyword in ['admin', 'system', 'default', 'super']):
                    empty_orgs.append(org)
            
            stats['orphaned_datasets'] = len(orphaned_datasets)
            stats['empty_organizations'] = len(empty_orgs)
            
            # User details
            users = session.query(User).all()
            stats['user_details'] = [
                {
                    'id': u.id,
                    'email': u.email,
                    'organization_id': u.organization_id,
                    'is_superuser': u.is_superuser
                }
                for u in users
            ]
            
            # Organization details
            orgs = session.query(Organization).all()
            stats['organization_details'] = [
                {
                    'id': o.id,
                    'name': o.name,
                    'user_count': session.query(User).filter(User.organization_id == o.id).count()
                }
                for o in orgs
            ]
            
            # Dataset details
            datasets = session.query(Dataset).all()
            stats['dataset_details'] = [
                {
                    'id': d.id,
                    'name': d.name,
                    'owner_id': d.owner_id,
                    'organization_id': d.organization_id,
                    'is_active': d.is_active,
                    'is_deleted': d.is_deleted,
                    'owner_exists': session.query(User).filter(User.id == d.owner_id).first() is not None
                }
                for d in datasets
            ]
            
            return stats
    
    def print_database_overview(self, stats: dict):
        """Print a formatted overview of the database state"""
        print("🗄️  Database Overview")
        print("=" * 60)
        
        print(f"\n📊 Basic Statistics:")
        print(f"  • Users: {stats['users']}")
        print(f"  • Organizations: {stats['organizations']}")
        print(f"  • Total Datasets: {stats['datasets']}")
        print(f"  • Active Datasets: {stats['active_datasets']}")
        print(f"  • Orphaned Datasets: {stats['orphaned_datasets']} ⚠️")
        print(f"  • Empty Organizations: {stats['empty_organizations']} ⚠️")
        
        print(f"\n👥 Users ({len(stats['user_details'])}):")
        for user in stats['user_details']:
            role = "🔑 Admin" if user['is_superuser'] else "👤 User"
            org_info = f"Org: {user['organization_id']}" if user['organization_id'] else "No org"
            print(f"  • {role} - {user['email']} (ID: {user['id']}, {org_info})")
        
        print(f"\n🏢 Organizations ({len(stats['organization_details'])}):")
        for org in stats['organization_details']:
            empty_flag = "📭" if org['user_count'] == 0 else "👥"
            print(f"  • {empty_flag} {org['name']} (ID: {org['id']}, Users: {org['user_count']})")
        
        print(f"\n📁 Datasets ({len(stats['dataset_details'])}):")
        for dataset in stats['dataset_details']:
            status_flags = []
            if not dataset['owner_exists']:
                status_flags.append("❌ Orphaned")
            if not dataset['is_active']:
                status_flags.append("😴 Inactive")
            if dataset['is_deleted']:
                status_flags.append("🗑️ Deleted")
            
            status_str = f" ({', '.join(status_flags)})" if status_flags else " ✅"
            print(f"  • {dataset['name']} (ID: {dataset['id']}, Owner: {dataset['owner_id']}){status_str}")
    
    def simulate_cleanup(self, stats: dict):
        """Show what would happen during cleanup without actually doing it"""
        print("\n🧹 Cleanup Simulation")
        print("=" * 60)
        
        if stats['orphaned_datasets'] > 0:
            print(f"\n🗑️  Would clean up {stats['orphaned_datasets']} orphaned datasets:")
            orphaned = [d for d in stats['dataset_details'] if not d['owner_exists']]
            for dataset in orphaned:
                print(f"  • {dataset['name']} (ID: {dataset['id']}, Owner: {dataset['owner_id']} - missing)")
        
        if stats['empty_organizations'] > 0:
            print(f"\n🏢 Would clean up {stats['empty_organizations']} empty organizations:")
            empty = [o for o in stats['organization_details'] if o['user_count'] == 0 
                    and not any(keyword in o['name'].lower() for keyword in ['admin', 'system', 'default', 'super'])]
            for org in empty:
                print(f"  • {org['name']} (ID: {org['id']})")
        
        if stats['orphaned_datasets'] == 0 and stats['empty_organizations'] == 0:
            print("\n✅ Database is clean! No cleanup needed.")

async def test_api_endpoints():
    """Test the API endpoints if available"""
    try:
        import httpx
        
        print("\n🌐 Testing API Endpoints")
        print("=" * 60)
        
        # You would need to get an admin token first
        print("Note: API endpoint testing requires admin authentication")
        print("Available endpoints:")
        print("  • GET /api/admin/cleanup/stats - Get cleanup statistics")
        print("  • POST /api/admin/cleanup/orphaned-datasets?confirm=true - Cleanup orphaned datasets")
        print("  • POST /api/admin/cleanup/empty-organizations?confirm=true - Cleanup empty organizations")
        print("  • POST /api/admin/cleanup/all?confirm=true - Cleanup all orphaned data")
        
    except ImportError:
        print("\n📝 Note: Install httpx to test API endpoints: pip install httpx")

def main():
    parser = argparse.ArgumentParser(description='Test database cleanup functionality')
    parser.add_argument('--run-cleanup', action='store_true', help='Actually run the cleanup (DESTRUCTIVE)')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')
    parser.add_argument('--api-test', action='store_true', help='Test API endpoints')
    
    args = parser.parse_args()
    
    tester = CleanupTester()
    
    print("🧪 Database Cleanup Test Suite")
    print("=" * 60)
    print(f"⏰ Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get initial database state
    print("\n📸 Taking database snapshot...")
    initial_stats = tester.get_database_overview()
    tester.print_database_overview(initial_stats)
    
    # Show what cleanup would do
    tester.simulate_cleanup(initial_stats)
    
    if args.run_cleanup:
        if initial_stats['orphaned_datasets'] == 0 and initial_stats['empty_organizations'] == 0:
            print("\n✅ No cleanup needed - database is already clean!")
        else:
            if not args.force:
                print(f"\n⚠️  WARNING: This will PERMANENTLY DELETE:")
                print(f"  • {initial_stats['orphaned_datasets']} orphaned datasets")
                print(f"  • {initial_stats['empty_organizations']} empty organizations")
                response = input("\n❓ Are you sure you want to proceed? (y/N): ")
                if response.lower() != 'y':
                    print("🛑 Cleanup cancelled.")
                    return
            
            # Import and run the actual cleanup
            from database_cleanup import DatabaseCleanup
            
            print("\n🚀 Running actual cleanup...")
            cleanup = DatabaseCleanup()
            
            if initial_stats['orphaned_datasets'] > 0:
                cleanup.cleanup_orphaned_datasets(dry_run=False)
            
            if initial_stats['empty_organizations'] > 0:
                cleanup.cleanup_empty_organizations(dry_run=False)
            
            # Get final state
            print("\n📸 Taking final database snapshot...")
            final_stats = tester.get_database_overview()
            tester.print_database_overview(final_stats)
            
            # Show summary
            print("\n📈 Cleanup Summary:")
            print(f"  • Datasets cleaned: {initial_stats['orphaned_datasets'] - final_stats['orphaned_datasets']}")
            print(f"  • Organizations cleaned: {initial_stats['empty_organizations'] - final_stats['empty_organizations']}")
    
    if args.api_test:
        asyncio.run(test_api_endpoints())
    
    print(f"\n✅ Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()