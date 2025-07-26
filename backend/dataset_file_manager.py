#!/usr/bin/env python3
"""
Dataset File Manager - A file manager-like interface for viewing dataset files
Shows datasets organized by type with file information
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class DatasetFileManager:
    def __init__(self, db_path: str = "storage/aishare_platform.db", storage_path: str = "storage"):
        self.db_path = db_path
        self.storage_path = storage_path
        
    def get_datasets_info(self) -> List[Dict[str, Any]]:
        """Get all datasets with their file information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
        SELECT 
            id, name, type, file_path, size_bytes, 
            created_at, is_active, is_deleted, download_count,
            description, status
        FROM datasets 
        ORDER BY type, name
        """
        
        cursor.execute(query)
        datasets = []
        
        for row in cursor.fetchall():
            dataset = {
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'file_path': row[3],
                'size_bytes': row[4] or 0,
                'created_at': row[5],
                'is_active': row[6],
                'is_deleted': row[7],
                'download_count': row[8] or 0,
                'description': row[9],
                'status': row[10]
            }
            
            # Add file system information
            if dataset['file_path']:
                full_path = os.path.join(self.storage_path, dataset['file_path'])
                dataset['file_exists'] = os.path.exists(full_path)
                if dataset['file_exists']:
                    stat = os.stat(full_path)
                    dataset['actual_size'] = stat.st_size
                    dataset['modified_at'] = datetime.fromtimestamp(stat.st_mtime)
                    dataset['file_extension'] = Path(full_path).suffix.lower()
                else:
                    dataset['actual_size'] = 0
                    dataset['modified_at'] = None
                    dataset['file_extension'] = ''
            else:
                dataset['file_exists'] = False
                dataset['actual_size'] = 0
                dataset['modified_at'] = None
                dataset['file_extension'] = ''
                
            datasets.append(dataset)
        
        conn.close()
        return datasets
    
    def format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(size_bytes)
        unit_index = 0
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.1f} {units[unit_index]}"
    
    def get_status_icon(self, dataset: Dict[str, Any]) -> str:
        """Get status icon for dataset"""
        if dataset['is_deleted']:
            return "🗑️"
        elif not dataset['is_active']:
            return "⏸️"
        elif not dataset['file_exists']:
            return "❌"
        else:
            return "✅"
    
    def get_type_icon(self, file_type: str) -> str:
        """Get icon for file type"""
        type_icons = {
            'PDF': '📄',
            'CSV': '📊',
            'JSON': '📋',
            'EXCEL': '📈',
            'TXT': '📝',
            'IMAGE': '🖼️',
            'VIDEO': '🎥',
            'AUDIO': '🎵'
        }
        return type_icons.get(file_type.upper(), '📁')
    
    def display_file_manager(self):
        """Display datasets in a file manager-like format"""
        datasets = self.get_datasets_info()
        
        if not datasets:
            print("📂 No datasets found")
            return
        
        # Group by type
        grouped = {}
        for dataset in datasets:
            file_type = dataset['type'] or 'UNKNOWN'
            if file_type not in grouped:
                grouped[file_type] = []
            grouped[file_type].append(dataset)
        
        print("\n" + "="*80)
        print("📁 DATASET FILE MANAGER")
        print("="*80)
        
        total_files = len(datasets)
        total_size = sum(d['actual_size'] for d in datasets if d['file_exists'])
        active_files = len([d for d in datasets if d['is_active'] and not d['is_deleted']])
        
        print(f"📊 Summary: {total_files} files | {active_files} active | {self.format_size(total_size)} total")
        print()
        
        for file_type, type_datasets in sorted(grouped.items()):
            type_icon = self.get_type_icon(file_type)
            print(f"📂 {type_icon} {file_type} Files ({len(type_datasets)})")
            print("─" * 78)
            
            for dataset in sorted(type_datasets, key=lambda x: x['name']):
                status_icon = self.get_status_icon(dataset)
                size_str = self.format_size(dataset['actual_size'])
                downloads = dataset['download_count']
                
                # Truncate name if too long
                name = dataset['name'][:45] + "..." if len(dataset['name']) > 45 else dataset['name']
                
                print(f"  {status_icon} {name:<48} {size_str:>8} {downloads:>3}↓")
                
                # Show file path if different from name
                if dataset['file_path']:
                    file_name = os.path.basename(dataset['file_path'])
                    if file_name != dataset['name']:
                        print(f"     📎 {dataset['file_path']}")
                
                # Show issues
                issues = []
                if dataset['is_deleted']:
                    issues.append("DELETED")
                elif not dataset['is_active']:
                    issues.append("INACTIVE")
                if not dataset['file_exists']:
                    issues.append("FILE MISSING")
                if dataset['size_bytes'] != dataset['actual_size'] and dataset['file_exists']:
                    issues.append("SIZE MISMATCH")
                
                if issues:
                    print(f"     ⚠️  {', '.join(issues)}")
            
            print()
        
        print("Legend: ✅ Active | ⏸️ Inactive | 🗑️ Deleted | ❌ Missing | ↓ Downloads")
        print("="*80)
    
    def display_detailed_info(self, dataset_id: int):
        """Display detailed information for a specific dataset"""
        datasets = self.get_datasets_info()
        dataset = next((d for d in datasets if d['id'] == dataset_id), None)
        
        if not dataset:
            print(f"❌ Dataset with ID {dataset_id} not found")
            return
        
        print("\n" + "="*60)
        print(f"📄 DATASET DETAILS - ID: {dataset['id']}")
        print("="*60)
        
        status_icon = self.get_status_icon(dataset)
        type_icon = self.get_type_icon(dataset['type'])
        
        print(f"Name:        {status_icon} {dataset['name']}")
        print(f"Type:        {type_icon} {dataset['type']}")
        print(f"File Path:   {dataset['file_path'] or 'N/A'}")
        print(f"Size:        {self.format_size(dataset['actual_size'])} ({dataset['actual_size']:,} bytes)")
        print(f"Downloads:   {dataset['download_count']}")
        print(f"Created:     {dataset['created_at']}")
        if dataset['modified_at']:
            print(f"Modified:    {dataset['modified_at']}")
        print(f"Active:      {'Yes' if dataset['is_active'] else 'No'}")
        print(f"Deleted:     {'Yes' if dataset['is_deleted'] else 'No'}")
        print(f"File Exists: {'Yes' if dataset['file_exists'] else 'No'}")
        
        if dataset['description']:
            print(f"Description: {dataset['description']}")
        if dataset['status']:
            print(f"Status:      {dataset['status']}")
        
        print("="*60)

def main():
    """Main function to run the file manager"""
    manager = DatasetFileManager()
    
    while True:
        print("\n🗂️  Dataset File Manager")
        print("1. View all datasets (file manager view)")
        print("2. View dataset details")
        print("3. Exit")
        
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == '1':
            manager.display_file_manager()
        elif choice == '2':
            try:
                dataset_id = int(input("Enter dataset ID: ").strip())
                manager.display_detailed_info(dataset_id)
            except ValueError:
                print("❌ Please enter a valid dataset ID")
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please select 1-3.")

if __name__ == "__main__":
    main()