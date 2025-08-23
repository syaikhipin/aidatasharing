#!/usr/bin/env python3
"""
Database Cleanup Script - Remove Orphaned Data

This script cleans up:
1. Datasets that don't belong to any existing user (orphaned datasets)
2. Organizations that have no users (except admin organizations)
3. Related data that depends on removed entities

Usage:
    python database_cleanup.py [--dry-run] [--force]
    
Options:
    --dry-run: Show what would be deleted without actually deleting
    --force: Skip confirmation prompts
"""

import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Tuple

# Add the backend directory to the Python path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.database import Base
from app.models.user import User
from app.models.organization import Organization
from app.models.dataset import (
    Dataset, DatasetAccessLog, DatasetDownload, DatasetModel, 
    DatasetChatSession, ChatMessage, DatasetShareAccess, DatabaseConnector
)

# Database configuration
DATABASE_URL = "sqlite:///storage/aishare_platform.db"

class DatabaseCleanup:
    def __init__(self, database_url: str = DATABASE_URL):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def get_orphaned_datasets(self, session: Session) -> List[Dataset]:
        """Find datasets that don't belong to any existing user"""
        orphaned_datasets = session.query(Dataset).filter(
            ~Dataset.owner_id.in_(session.query(User.id))
        ).all()
        return orphaned_datasets
    
    def get_empty_organizations(self, session: Session) -> List[Organization]:
        """Find organizations with no users (excluding admin organizations)"""
        # Get organizations with no users
        empty_orgs = session.query(Organization).filter(
            ~Organization.id.in_(session.query(User.organization_id).filter(User.organization_id.isnot(None)))
        ).all()
        
        # Filter out admin organizations (those with admin/superuser patterns)
        non_admin_empty_orgs = []
        for org in empty_orgs:
            # Skip organizations that might be admin-related
            if not any(keyword in org.name.lower() for keyword in ['admin', 'system', 'default', 'super']):
                non_admin_empty_orgs.append(org)
                
        return non_admin_empty_orgs
    
    def get_related_data_counts(self, session: Session, dataset_ids: List[int]) -> Dict[str, int]:
        """Get counts of related data that will be affected"""
        if not dataset_ids:
            return {}
            
        counts = {}
        
        # Access logs
        counts['access_logs'] = session.query(DatasetAccessLog).filter(
            DatasetAccessLog.dataset_id.in_(dataset_ids)
        ).count()
        
        # Downloads
        counts['downloads'] = session.query(DatasetDownload).filter(
            DatasetDownload.dataset_id.in_(dataset_ids)
        ).count()
        
        # Models
        counts['models'] = session.query(DatasetModel).filter(
            DatasetModel.dataset_id.in_(dataset_ids)
        ).count()
        
        # Chat sessions
        chat_sessions = session.query(DatasetChatSession).filter(
            DatasetChatSession.dataset_id.in_(dataset_ids)
        ).all()
        counts['chat_sessions'] = len(chat_sessions)
        
        # Chat messages
        if chat_sessions:
            session_ids = [cs.id for cs in chat_sessions]
            counts['chat_messages'] = session.query(ChatMessage).filter(
                ChatMessage.session_id.in_(session_ids)
            ).count()
        else:
            counts['chat_messages'] = 0
        
        # Share accesses
        counts['share_accesses'] = session.query(DatasetShareAccess).filter(
            DatasetShareAccess.dataset_id.in_(dataset_ids)
        ).count()
        
        return counts
    
    def get_organization_related_data_counts(self, session: Session, org_ids: List[int]) -> Dict[str, int]:
        """Get counts of organization-related data that will be affected"""
        if not org_ids:
            return {}
            
        counts = {}
        
        # Database connectors
        counts['connectors'] = session.query(DatabaseConnector).filter(
            DatabaseConnector.organization_id.in_(org_ids)
        ).count()
        
        # Datasets belonging to these organizations
        counts['org_datasets'] = session.query(Dataset).filter(
            Dataset.organization_id.in_(org_ids)
        ).count()
        
        return counts
    
    def delete_dataset_related_data(self, session: Session, dataset_ids: List[int], dry_run: bool = False):
        """Delete all data related to the given datasets"""
        if not dataset_ids:
            return
            
        print(f"{'[DRY RUN] ' if dry_run else ''}Cleaning up related data for {len(dataset_ids)} datasets...")
        
        # Delete chat messages first (foreign key dependency)
        chat_sessions = session.query(DatasetChatSession).filter(
            DatasetChatSession.dataset_id.in_(dataset_ids)
        ).all()
        
        if chat_sessions:
            session_ids = [cs.id for cs in chat_sessions]
            chat_messages_count = session.query(ChatMessage).filter(
                ChatMessage.session_id.in_(session_ids)
            ).count()
            
            if not dry_run:
                session.query(ChatMessage).filter(
                    ChatMessage.session_id.in_(session_ids)
                ).delete(synchronize_session=False)
            print(f"{'[DRY RUN] ' if dry_run else ''}  - Deleted {chat_messages_count} chat messages")
        
        # Delete chat sessions
        chat_sessions_count = len(chat_sessions)
        if not dry_run:
            session.query(DatasetChatSession).filter(
                DatasetChatSession.dataset_id.in_(dataset_ids)
            ).delete(synchronize_session=False)
        print(f"{'[DRY RUN] ' if dry_run else ''}  - Deleted {chat_sessions_count} chat sessions")
        
        # Delete access logs
        access_logs_count = session.query(DatasetAccessLog).filter(
            DatasetAccessLog.dataset_id.in_(dataset_ids)
        ).count()
        if not dry_run:
            session.query(DatasetAccessLog).filter(
                DatasetAccessLog.dataset_id.in_(dataset_ids)
            ).delete(synchronize_session=False)
        print(f"{'[DRY RUN] ' if dry_run else ''}  - Deleted {access_logs_count} access logs")
        
        # Delete downloads
        downloads_count = session.query(DatasetDownload).filter(
            DatasetDownload.dataset_id.in_(dataset_ids)
        ).count()
        if not dry_run:
            session.query(DatasetDownload).filter(
                DatasetDownload.dataset_id.in_(dataset_ids)
            ).delete(synchronize_session=False)
        print(f"{'[DRY RUN] ' if dry_run else ''}  - Deleted {downloads_count} downloads")
        
        # Delete models
        models_count = session.query(DatasetModel).filter(
            DatasetModel.dataset_id.in_(dataset_ids)
        ).count()
        if not dry_run:
            session.query(DatasetModel).filter(
                DatasetModel.dataset_id.in_(dataset_ids)
            ).delete(synchronize_session=False)
        print(f"{'[DRY RUN] ' if dry_run else ''}  - Deleted {models_count} models")
        
        # Delete share accesses
        share_accesses_count = session.query(DatasetShareAccess).filter(
            DatasetShareAccess.dataset_id.in_(dataset_ids)
        ).count()
        if not dry_run:
            session.query(DatasetShareAccess).filter(
                DatasetShareAccess.dataset_id.in_(dataset_ids)
            ).delete(synchronize_session=False)
        print(f"{'[DRY RUN] ' if dry_run else ''}  - Deleted {share_accesses_count} share accesses")
    
    def delete_organization_related_data(self, session: Session, org_ids: List[int], dry_run: bool = False):
        """Delete all data related to the given organizations"""
        if not org_ids:
            return
            
        print(f"{'[DRY RUN] ' if dry_run else ''}Cleaning up organization-related data for {len(org_ids)} organizations...")
        
        # Delete database connectors
        connectors_count = session.query(DatabaseConnector).filter(
            DatabaseConnector.organization_id.in_(org_ids)
        ).count()
        if not dry_run:
            session.query(DatabaseConnector).filter(
                DatabaseConnector.organization_id.in_(org_ids)
            ).delete(synchronize_session=False)
        print(f"{'[DRY RUN] ' if dry_run else ''}  - Deleted {connectors_count} database connectors")
    
    def cleanup_orphaned_datasets(self, dry_run: bool = False) -> Tuple[int, Dict[str, int]]:
        """Remove orphaned datasets and their related data"""
        with self.SessionLocal() as session:
            # Find orphaned datasets
            orphaned_datasets = self.get_orphaned_datasets(session)
            
            if not orphaned_datasets:
                print("✅ No orphaned datasets found.")
                return 0, {}
            
            dataset_ids = [d.id for d in orphaned_datasets]
            related_counts = self.get_related_data_counts(session, dataset_ids)
            
            print(f"\n🗑️  Found {len(orphaned_datasets)} orphaned datasets:")
            for dataset in orphaned_datasets:
                print(f"  - ID: {dataset.id}, Name: '{dataset.name}', Owner ID: {dataset.owner_id} (missing)")
            
            print(f"\n📊 Related data that will be cleaned up:")
            for data_type, count in related_counts.items():
                if count > 0:
                    print(f"  - {data_type}: {count}")
            
            if not dry_run:
                # Delete related data first
                self.delete_dataset_related_data(session, dataset_ids, dry_run=False)
                
                # Delete the datasets themselves
                deleted_count = session.query(Dataset).filter(Dataset.id.in_(dataset_ids)).delete(synchronize_session=False)
                session.commit()
                
                print(f"\n✅ Successfully deleted {deleted_count} orphaned datasets and all related data.")
            else:
                print(f"\n[DRY RUN] Would delete {len(orphaned_datasets)} orphaned datasets and all related data.")
            
            return len(orphaned_datasets), related_counts
    
    def cleanup_empty_organizations(self, dry_run: bool = False) -> Tuple[int, Dict[str, int]]:
        """Remove empty organizations and their related data"""
        with self.SessionLocal() as session:
            # Find empty organizations
            empty_orgs = self.get_empty_organizations(session)
            
            if not empty_orgs:
                print("✅ No empty organizations found.")
                return 0, {}
            
            org_ids = [o.id for o in empty_orgs]
            related_counts = self.get_organization_related_data_counts(session, org_ids)
            
            print(f"\n🏢 Found {len(empty_orgs)} empty organizations:")
            for org in empty_orgs:
                print(f"  - ID: {org.id}, Name: '{org.name}', Type: {org.type}")
            
            print(f"\n📊 Organization-related data that will be cleaned up:")
            for data_type, count in related_counts.items():
                if count > 0:
                    print(f"  - {data_type}: {count}")
            
            if not dry_run:
                # Delete related data first
                self.delete_organization_related_data(session, org_ids, dry_run=False)
                
                # Delete the organizations themselves
                deleted_count = session.query(Organization).filter(Organization.id.in_(org_ids)).delete(synchronize_session=False)
                session.commit()
                
                print(f"\n✅ Successfully deleted {deleted_count} empty organizations and all related data.")
            else:
                print(f"\n[DRY RUN] Would delete {len(empty_orgs)} empty organizations and all related data.")
            
            return len(empty_orgs), related_counts
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get current database statistics"""
        with self.SessionLocal() as session:
            stats = {
                'users': session.query(User).count(),
                'organizations': session.query(Organization).count(),
                'datasets': session.query(Dataset).count(),
                'active_datasets': session.query(Dataset).filter(Dataset.is_active == True, Dataset.is_deleted == False).count(),
                'orphaned_datasets': len(self.get_orphaned_datasets(session)),
                'empty_organizations': len(self.get_empty_organizations(session)),
                'database_connectors': session.query(DatabaseConnector).count(),
            }
        return stats


def main():
    parser = argparse.ArgumentParser(description='Clean up orphaned datasets and empty organizations')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')
    parser.add_argument('--stats-only', action='store_true', help='Only show database statistics')
    
    args = parser.parse_args()
    
    cleanup = DatabaseCleanup()
    
    print("🧹 Database Cleanup Tool")
    print("=" * 50)
    
    # Show current database statistics
    print("\n📊 Current Database Statistics:")
    stats = cleanup.get_database_stats()
    for key, value in stats.items():
        print(f"  - {key.replace('_', ' ').title()}: {value}")
    
    if args.stats_only:
        return
    
    if stats['orphaned_datasets'] == 0 and stats['empty_organizations'] == 0:
        print("\n✅ Database is clean! No orphaned data found.")
        return
    
    print(f"\n⚠️  Found issues that need cleanup:")
    if stats['orphaned_datasets'] > 0:
        print(f"  - {stats['orphaned_datasets']} orphaned datasets")
    if stats['empty_organizations'] > 0:
        print(f"  - {stats['empty_organizations']} empty organizations")
    
    if not args.dry_run and not args.force:
        response = input("\n❓ Do you want to proceed with cleanup? (y/N): ")
        if response.lower() != 'y':
            print("🛑 Cleanup cancelled.")
            return
    
    print(f"\n🚀 Starting cleanup {'(DRY RUN MODE)' if args.dry_run else '(LIVE MODE)'}...")
    print("-" * 50)
    
    # Cleanup orphaned datasets
    if stats['orphaned_datasets'] > 0:
        orphaned_count, orphaned_related = cleanup.cleanup_orphaned_datasets(dry_run=args.dry_run)
    
    # Cleanup empty organizations
    if stats['empty_organizations'] > 0:
        empty_count, empty_related = cleanup.cleanup_empty_organizations(dry_run=args.dry_run)
    
    # Show final statistics
    print("\n📊 Final Database Statistics:")
    final_stats = cleanup.get_database_stats()
    for key, value in final_stats.items():
        change = ""
        if key in stats and stats[key] != value:
            change = f" (was {stats[key]})"
        print(f"  - {key.replace('_', ' ').title()}: {value}{change}")
    
    if args.dry_run:
        print("\n💡 Run without --dry-run to actually perform the cleanup.")
    else:
        print(f"\n✅ Cleanup completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()