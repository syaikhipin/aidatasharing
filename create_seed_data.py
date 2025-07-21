#!/usr/bin/env python3
"""
Script to create comprehensive seed data for the AI Share Platform
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
import random

def create_seed_data():
    """Create comprehensive seed data."""
    db_path = "backend/storage/aishare_platform.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🌱 Creating seed data...")
        
        # Get admin user and organization IDs
        cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@example.com",))
        admin_user = cursor.fetchone()
        admin_user_id = admin_user[0] if admin_user else 1
        
        cursor.execute("SELECT id FROM organizations WHERE slug = ?", ("default-org",))
        org_result = cursor.fetchone()
        org_id = org_result[0] if org_result else 1
        
        # Create sample datasets
        print("📊 Creating sample datasets...")
        datasets = [
            {
                "name": "Customer Sales Data",
                "description": "Comprehensive sales data including customer demographics, purchase history, and revenue metrics",
                "file_path": "/storage/uploads/customer_sales.csv",
                "size_bytes": 2048576,
                "type": "csv",
                "status": "active",
                "public_share_enabled": True,
                "owner_id": admin_user_id,
                "organization_id": org_id,
                "tags": "sales,customer,revenue,analytics",
                "row_count": 15000,
                "column_count": 6,
                "file_metadata": json.dumps({
                    "columns": ["customer_id", "name", "email", "purchase_date", "amount", "product_category"],
                    "file_format": "CSV",
                    "encoding": "UTF-8"
                })
            },
            {
                "name": "Product Inventory",
                "description": "Real-time inventory data with stock levels, pricing, and supplier information",
                "file_path": "/storage/uploads/inventory.xlsx",
                "size_bytes": 1024000,
                "type": "xlsx",
                "status": "active",
                "public_share_enabled": False,
                "owner_id": admin_user_id,
                "organization_id": org_id,
                "tags": "inventory,products,stock,suppliers",
                "row_count": 5000,
                "column_count": 6,
                "file_metadata": json.dumps({
                    "columns": ["product_id", "name", "category", "stock_level", "price", "supplier"],
                    "file_format": "Excel",
                    "sheets": ["Products", "Suppliers"]
                })
            },
            {
                "name": "Employee Performance Metrics",
                "description": "HR analytics data including performance reviews, training records, and career progression",
                "file_path": "/storage/uploads/hr_metrics.json",
                "size_bytes": 512000,
                "type": "json",
                "status": "active",
                "public_share_enabled": False,
                "owner_id": admin_user_id,
                "organization_id": org_id,
                "tags": "hr,performance,employees,analytics",
                "row_count": 250,
                "column_count": 8,
                "file_metadata": json.dumps({
                    "structure": "nested_json",
                    "employee_count": 250,
                    "metrics": ["performance_score", "training_hours", "projects_completed"]
                })
            },
            {
                "name": "Marketing Campaign Results",
                "description": "Digital marketing campaign performance data with ROI, conversion rates, and audience insights",
                "file_path": "/storage/uploads/marketing_data.csv",
                "size_bytes": 3072000,
                "type": "csv",
                "status": "active",
                "public_share_enabled": True,
                "owner_id": admin_user_id,
                "organization_id": org_id,
                "tags": "marketing,campaigns,roi,conversion",
                "row_count": 8500,
                "column_count": 6,
                "file_metadata": json.dumps({
                    "columns": ["campaign_id", "platform", "spend", "impressions", "clicks", "conversions"],
                    "date_range": "2024-01-01 to 2024-12-31"
                })
            },
            {
                "name": "Financial Reports Q4 2024",
                "description": "Quarterly financial statements, budget analysis, and expense tracking",
                "file_path": "/storage/uploads/financial_q4.xlsx",
                "size_bytes": 1536000,
                "type": "xlsx",
                "status": "active",
                "public_share_enabled": False,
                "owner_id": admin_user_id,
                "organization_id": org_id,
                "tags": "finance,quarterly,budget,expenses",
                "row_count": 2500,
                "column_count": 12,
                "file_metadata": json.dumps({
                    "sheets": ["Income Statement", "Balance Sheet", "Cash Flow"],
                    "period": "Q4 2024",
                    "currency": "USD"
                })
            }
        ]
        
        dataset_ids = []
        for dataset in datasets:
            cursor.execute("""
                INSERT INTO datasets (name, description, file_path, size_bytes, type, status, public_share_enabled, 
                                    owner_id, organization_id, row_count, column_count, file_metadata, 
                                    created_at, updated_at, is_active, is_deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 1, 0)
            """, (
                dataset["name"], dataset["description"], dataset["file_path"], dataset["size_bytes"],
                dataset["type"], dataset["status"], dataset["public_share_enabled"], dataset["owner_id"],
                dataset["organization_id"], dataset["row_count"], dataset["column_count"],
                dataset["file_metadata"]
            ))
            dataset_ids.append(cursor.lastrowid)
        
        print(f"   ✅ Created {len(datasets)} sample datasets")
        
        # Create access requests
        print("📝 Creating access requests...")
        request_types = ["access", "download", "share"]
        access_levels = ["read", "write", "admin"]
        statuses = ["pending", "approved", "rejected"]
        categories = ["research", "analysis", "compliance", "reporting", "development"]
        urgencies = ["low", "medium", "high"]
        
        for i in range(10):
            dataset_id = random.choice(dataset_ids)
            request_type = random.choice(request_types)
            access_level = random.choice(access_levels)
            status = random.choice(statuses)
            category = random.choice(categories)
            urgency = random.choice(urgencies)
            
            cursor.execute("""
                INSERT INTO access_requests (requester_id, dataset_id, request_type, requested_level, 
                                           purpose, justification, urgency, category, status, 
                                           created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '-' || ? || ' days'))
            """, (
                admin_user_id, dataset_id, request_type, access_level,
                f"Request for {request_type} access to dataset for {category} purposes",
                f"Need {access_level} access for {category} work and data analysis",
                urgency, category, status,
                random.randint(1, 30)
            ))
        
        print("   ✅ Created 10 access requests")
        
        # Create audit logs
        print("📋 Creating audit logs...")
        actions = [
            "user_login", "user_logout", "dataset_upload", "dataset_download", "dataset_share",
            "access_request_created", "access_request_approved", "access_request_rejected",
            "user_created", "organization_created", "configuration_updated"
        ]
        
        for i in range(25):
            action = random.choice(actions)
            dataset_id = random.choice(dataset_ids)
            
            details = {
                "user_login": "User successfully logged in",
                "user_logout": "User logged out",
                "dataset_upload": f"Dataset uploaded: {datasets[i % len(datasets)]['name']}",
                "dataset_download": f"Dataset downloaded: {datasets[i % len(datasets)]['name']}",
                "dataset_share": f"Dataset shared: {datasets[i % len(datasets)]['name']}",
                "access_request_created": "New access request submitted",
                "access_request_approved": "Access request approved by admin",
                "access_request_rejected": "Access request rejected",
                "user_created": "New user account created",
                "organization_created": "New organization created",
                "configuration_updated": "System configuration updated"
            }[action]
            
            cursor.execute("""
                INSERT INTO audit_logs (user_id, action, details, dataset_id, ip_address, user_agent,
                                      timestamp)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now', '-' || ? || ' hours'))
            """, (
                admin_user_id, action, details, dataset_id,
                f"192.168.1.{random.randint(100, 200)}",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                random.randint(1, 720)  # Last 30 days
            ))
        
        print("   ✅ Created 25 audit log entries")
        
        # Create system metrics
        print("📊 Creating system metrics...")
        for i in range(24):  # Last 24 hours
            cursor.execute("""
                INSERT INTO system_metrics (timestamp, cpu_usage_percent, memory_usage_percent, disk_usage_percent,
                                          active_connections, total_datasets, total_users, total_organizations,
                                          active_sessions, requests_per_minute, avg_response_time_ms,
                                          total_storage_bytes, available_storage_bytes, mindsdb_health,
                                          mindsdb_response_time_ms)
                VALUES (datetime('now', '-' || ? || ' hours'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                i,  # Hours ago
                random.uniform(20, 80),  # CPU usage
                random.uniform(40, 90),  # Memory usage
                random.uniform(30, 85),  # Disk usage
                random.randint(5, 50),   # Active connections
                random.randint(10, 100), # Total datasets
                random.randint(5, 50),   # Total users
                random.randint(1, 10),   # Total organizations
                random.randint(1, 20),   # Active sessions
                random.uniform(10, 100), # Requests per minute
                random.uniform(50, 500), # Avg response time
                random.randint(1000000, 10000000000),  # Total storage bytes
                random.randint(500000, 5000000000),    # Available storage bytes
                random.choice(["healthy", "warning", "error"]),  # MindsDB health
                random.uniform(100, 1000)  # MindsDB response time
            ))
        
        print("   ✅ Created 24 system metrics entries")
        
        # Create dataset access logs
        print("🔍 Creating dataset access logs...")
        access_types = ["view", "download", "share", "chat"]
        access_methods = ["web", "api", "direct"]
        
        for i in range(50):
            dataset_id = random.choice(dataset_ids)
            access_type = random.choice(access_types)
            access_method = random.choice(access_methods)
            
            cursor.execute("""
                INSERT INTO dataset_access (access_id, dataset_id, user_id, access_type, access_method,
                                          ip_address, user_agent, timestamp, duration_seconds, 
                                          organization_id, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', '-' || ? || ' hours'), ?, ?, ?)
            """, (
                f"access_{i}_{random.randint(1000, 9999)}",  # access_id
                dataset_id, admin_user_id, access_type, access_method,
                f"192.168.1.{random.randint(100, 200)}",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                random.randint(1, 168),  # Last week
                random.uniform(10, 300),  # Duration in seconds
                org_id,  # organization_id
                True  # success
            ))
        
        print("   ✅ Created 50 dataset access logs")
        
        # Create additional test users
        print("👥 Creating additional test users...")
        test_users = [
            {"email": "john.doe@demo.com", "name": "John Doe", "role": "analyst"},
            {"email": "jane.smith@demo.com", "name": "Jane Smith", "role": "manager"},
            {"email": "bob.wilson@demo.com", "name": "Bob Wilson", "role": "member"},
            {"email": "alice.brown@demo.com", "name": "Alice Brown", "role": "member"}
        ]
        
        for user in test_users:
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (user["email"],))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO users (email, hashed_password, full_name, is_active, is_superuser,
                                     organization_id, role, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """, (
                    user["email"], "$2b$12$dummy.hash.for.demo.purposes.only",
                    user["name"], True, False, org_id, user["role"]
                ))
        
        print("   ✅ Created 4 additional test users")
        
        conn.commit()
        print("\n🎉 Seed data creation completed successfully!")
        
        # Show summary
        print("\n📊 Database Summary:")
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"   - Users: {user_count}")
        
        cursor.execute("SELECT COUNT(*) FROM datasets")
        dataset_count = cursor.fetchone()[0]
        print(f"   - Datasets: {dataset_count}")
        
        cursor.execute("SELECT COUNT(*) FROM access_requests")
        request_count = cursor.fetchone()[0]
        print(f"   - Access Requests: {request_count}")
        
        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        audit_count = cursor.fetchone()[0]
        print(f"   - Audit Logs: {audit_count}")
        
        cursor.execute("SELECT COUNT(*) FROM system_metrics")
        metrics_count = cursor.fetchone()[0]
        print(f"   - System Metrics: {metrics_count}")
        
        cursor.execute("SELECT COUNT(*) FROM dataset_access")
        access_count = cursor.fetchone()[0]
        print(f"   - Dataset Access Logs: {access_count}")
        
    except Exception as e:
        print(f"❌ Error creating seed data: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_seed_data()