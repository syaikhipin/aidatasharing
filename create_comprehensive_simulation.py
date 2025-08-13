#!/usr/bin/env python3
"""
Comprehensive Simulation Script for AI Share Platform
Creates multiple users, organizations, and diverse datasets with various sharing levels
for comprehensive manual testing of the platform functionality.
"""

import sys
import os
import asyncio
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import get_db
from app.models.dataset import Dataset, DatasetType, DatasetStatus, DataSharingLevel
from app.models.user import User
from app.models.organization import Organization
from app.core.auth import get_password_hash
from app.services.mindsdb import MindsDBService

class SimulationDataGenerator:
    """Generate realistic simulation data for testing."""
    
    def __init__(self):
        self.organizations = [
            {
                "name": "TechCorp Industries",
                "slug": "techcorp-industries",
                "description": "Leading technology corporation focused on AI and data analytics",
                "is_active": True
            },
            {
                "name": "DataScience Hub",
                "slug": "datascience-hub",
                "description": "Community-driven data science research organization",
                "is_active": True
            },
            {
                "name": "StartupLab",
                "slug": "startuplab",
                "description": "Innovation lab for emerging startups and entrepreneurs",
                "is_active": True
            },
            {
                "name": "Academic Research Institute",
                "slug": "academic-research-institute",
                "description": "University-affiliated research institute for academic collaboration",
                "is_active": True
            }
        ]
        
        self.users = [
            # TechCorp Industries Users
            {"email": "alice.smith@techcorp.com", "password": "tech2024", "full_name": "Alice Smith", "role": "admin", "org_index": 0},
            {"email": "bob.johnson@techcorp.com", "password": "tech2024", "full_name": "Bob Johnson", "role": "analyst", "org_index": 0},
            {"email": "carol.williams@techcorp.com", "password": "tech2024", "full_name": "Carol Williams", "role": "member", "org_index": 0},
            
            # DataScience Hub Users
            {"email": "david.brown@datasci.org", "password": "data2024", "full_name": "David Brown", "role": "admin", "org_index": 1},
            {"email": "eva.davis@datasci.org", "password": "data2024", "full_name": "Eva Davis", "role": "researcher", "org_index": 1},
            {"email": "frank.miller@datasci.org", "password": "data2024", "full_name": "Frank Miller", "role": "member", "org_index": 1},
            
            # StartupLab Users
            {"email": "grace.wilson@startuplab.io", "password": "startup2024", "full_name": "Grace Wilson", "role": "founder", "org_index": 2},
            {"email": "henry.moore@startuplab.io", "password": "startup2024", "full_name": "Henry Moore", "role": "developer", "org_index": 2},
            
            # Academic Research Institute Users
            {"email": "iris.taylor@research.edu", "password": "research2024", "full_name": "Dr. Iris Taylor", "role": "professor", "org_index": 3},
            {"email": "jack.anderson@research.edu", "password": "research2024", "full_name": "Jack Anderson", "role": "student", "org_index": 3}
        ]
        
        self.web_connectors = [
            {
                "name": "GitHub Issues Tracker",
                "description": "Real-time GitHub issues data for project management analysis",
                "base_url": "https://api.github.com",
                "endpoint": "/repos/microsoft/vscode/issues",
                "method": "GET",
                "sharing_level": DataSharingLevel.PUBLIC
            },
            {
                "name": "Weather API Data",
                "description": "Current weather data for climate analysis and forecasting",
                "base_url": "https://api.openweathermap.org",
                "endpoint": "/data/2.5/weather?q=London",
                "method": "GET",
                "sharing_level": DataSharingLevel.ORGANIZATION
            },
            {
                "name": "JSON Placeholder Posts",
                "description": "Sample blog posts data for content analysis testing",
                "base_url": "https://jsonplaceholder.typicode.com",
                "endpoint": "/posts",
                "method": "GET",
                "sharing_level": DataSharingLevel.ORGANIZATION
            },
            {
                "name": "JSON Placeholder Users",
                "description": "Sample user data for demographic analysis",
                "base_url": "https://jsonplaceholder.typicode.com",
                "endpoint": "/users",
                "method": "GET",
                "sharing_level": DataSharingLevel.PRIVATE
            },
            {
                "name": "CoinGecko Crypto Prices",
                "description": "Real-time cryptocurrency price data for financial analysis",
                "base_url": "https://api.coingecko.com",
                "endpoint": "/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd",
                "method": "GET",
                "sharing_level": DataSharingLevel.PUBLIC
            }
        ]
        
        self.uploaded_datasets = [
            {
                "name": "Sales Performance Q1 2024",
                "description": "Quarterly sales data with regional breakdown and product categories",
                "type": DatasetType.CSV,
                "row_count": 5000,
                "column_count": 12,
                "size_bytes": 250000,
                "sharing_level": DataSharingLevel.ORGANIZATION,
                "columns": ["id", "date", "product_id", "product_name", "category", "quantity", "unit_price", "total_amount", "customer_id", "region", "sales_rep", "commission"],
                "sample_data": [
                    {"id": 1, "date": "2024-01-15", "product_id": "P001", "product_name": "Laptop Pro", "category": "Electronics", "quantity": 2, "unit_price": 1299.99, "total_amount": 2599.98, "customer_id": "C001", "region": "North", "sales_rep": "Alice Smith", "commission": 259.99},
                    {"id": 2, "date": "2024-01-16", "product_id": "P002", "product_name": "Wireless Mouse", "category": "Accessories", "quantity": 5, "unit_price": 29.99, "total_amount": 149.95, "customer_id": "C002", "region": "South", "sales_rep": "Bob Johnson", "commission": 14.99}
                ]
            },
            {
                "name": "Customer Feedback Analysis",
                "description": "Customer feedback and satisfaction survey results with sentiment analysis",
                "type": DatasetType.JSON,
                "row_count": 2500,
                "column_count": 8,
                "size_bytes": 180000,
                "sharing_level": DataSharingLevel.PRIVATE,
                "columns": ["feedback_id", "customer_id", "rating", "comment", "sentiment_score", "category", "date_submitted", "resolved"],
                "sample_data": [
                    {"feedback_id": "FB001", "customer_id": "C001", "rating": 5, "comment": "Excellent product quality and fast delivery!", "sentiment_score": 0.9, "category": "Product Quality", "date_submitted": "2024-01-20", "resolved": True},
                    {"feedback_id": "FB002", "customer_id": "C002", "rating": 3, "comment": "Good product but shipping was delayed", "sentiment_score": 0.2, "category": "Shipping", "date_submitted": "2024-01-21", "resolved": False}
                ]
            },
            {
                "name": "Financial Market Data",
                "description": "Historical stock prices and trading volumes for portfolio analysis",
                "type": DatasetType.CSV,
                "row_count": 10000,
                "column_count": 10,
                "size_bytes": 500000,
                "sharing_level": DataSharingLevel.PUBLIC,
                "columns": ["date", "symbol", "open_price", "high_price", "low_price", "close_price", "volume", "market_cap", "pe_ratio", "dividend_yield"],
                "sample_data": [
                    {"date": "2024-01-15", "symbol": "AAPL", "open_price": 185.50, "high_price": 187.20, "low_price": 184.80, "close_price": 186.95, "volume": 45000000, "market_cap": 2900000000000, "pe_ratio": 28.5, "dividend_yield": 0.52},
                    {"date": "2024-01-15", "symbol": "GOOGL", "open_price": 142.30, "high_price": 144.10, "low_price": 141.50, "close_price": 143.75, "volume": 32000000, "market_cap": 1800000000000, "pe_ratio": 25.2, "dividend_yield": 0.0}
                ]
            },
            {
                "name": "Research Publications Database",
                "description": "Academic research papers with citations and impact metrics",
                "type": DatasetType.JSON,
                "row_count": 1500,
                "column_count": 15,
                "size_bytes": 320000,
                "sharing_level": DataSharingLevel.ORGANIZATION,
                "columns": ["paper_id", "title", "authors", "journal", "publication_date", "abstract", "keywords", "citation_count", "impact_factor", "doi", "field", "institution", "funding_source", "open_access", "peer_reviewed"],
                "sample_data": [
                    {"paper_id": "P001", "title": "Machine Learning in Healthcare: A Comprehensive Review", "authors": ["Dr. Iris Taylor", "Dr. John Smith"], "journal": "Journal of Medical AI", "publication_date": "2024-01-10", "abstract": "This paper reviews recent advances in machine learning applications...", "keywords": ["machine learning", "healthcare", "AI"], "citation_count": 25, "impact_factor": 4.2, "doi": "10.1000/journal.2024.001", "field": "Computer Science", "institution": "Academic Research Institute", "funding_source": "NSF Grant", "open_access": True, "peer_reviewed": True}
                ]
            },
            {
                "name": "IoT Sensor Network Data",
                "description": "Environmental sensor readings from smart city infrastructure",
                "type": DatasetType.CSV,
                "row_count": 50000,
                "column_count": 9,
                "size_bytes": 800000,
                "sharing_level": DataSharingLevel.PRIVATE,
                "columns": ["timestamp", "sensor_id", "location", "temperature", "humidity", "air_quality", "noise_level", "light_intensity", "battery_level"],
                "sample_data": [
                    {"timestamp": "2024-01-15T10:00:00Z", "sensor_id": "S001", "location": "Downtown Plaza", "temperature": 22.5, "humidity": 65.2, "air_quality": 85, "noise_level": 45.3, "light_intensity": 750, "battery_level": 87},
                    {"timestamp": "2024-01-15T10:05:00Z", "sensor_id": "S002", "location": "Park Avenue", "temperature": 21.8, "humidity": 68.1, "air_quality": 92, "noise_level": 38.7, "light_intensity": 820, "battery_level": 91}
                ]
            },
            {
                "name": "E-commerce Transaction Log",
                "description": "Online store transaction data with user behavior analytics",
                "type": DatasetType.JSON,
                "row_count": 8000,
                "column_count": 14,
                "size_bytes": 450000,
                "sharing_level": DataSharingLevel.ORGANIZATION,
                "columns": ["transaction_id", "user_id", "session_id", "timestamp", "product_ids", "quantities", "total_amount", "payment_method", "shipping_address", "discount_applied", "referrer", "device_type", "browser", "conversion_funnel"],
                "sample_data": [
                    {"transaction_id": "T001", "user_id": "U001", "session_id": "S001", "timestamp": "2024-01-15T14:30:00Z", "product_ids": ["P001", "P002"], "quantities": [1, 2], "total_amount": 159.97, "payment_method": "credit_card", "shipping_address": "123 Main St", "discount_applied": 10.0, "referrer": "google", "device_type": "desktop", "browser": "chrome", "conversion_funnel": ["landing", "product_view", "cart", "checkout", "purchase"]}
                ]
            }
        ]

async def create_organizations(db, generator):
    """Create organizations for the simulation."""
    print("🏢 Creating Organizations...")
    created_orgs = []
    
    for org_data in generator.organizations:
        existing_org = db.query(Organization).filter(Organization.slug == org_data["slug"]).first()
        if not existing_org:
            new_org = Organization(**org_data)
            db.add(new_org)
            db.commit()
            db.refresh(new_org)
            created_orgs.append(new_org)
            print(f"  ✅ Created: {new_org.name}")
        else:
            created_orgs.append(existing_org)
            print(f"  📋 Exists: {existing_org.name}")
    
    return created_orgs

async def create_users(db, generator, organizations):
    """Create users for the simulation."""
    print("\n👥 Creating Users...")
    created_users = []
    
    for user_data in generator.users:
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing_user:
            new_user = User(
                email=user_data["email"],
                hashed_password=get_password_hash(user_data["password"]),
                full_name=user_data["full_name"],
                is_active=True,
                is_superuser=(user_data["role"] == "admin"),
                organization_id=organizations[user_data["org_index"]].id,
                role=user_data["role"]
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            created_users.append(new_user)
            print(f"  ✅ Created: {new_user.email} ({new_user.role}) - {organizations[user_data['org_index']].name}")
        else:
            created_users.append(existing_user)
            print(f"  📋 Exists: {existing_user.email}")
    
    return created_users

async def create_web_connector_datasets(db, generator, users, mindsdb_service):
    """Create web connector datasets."""
    print("\n🌐 Creating Web Connector Datasets...")
    created_datasets = []
    
    for i, connector_data in enumerate(generator.web_connectors):
        try:
            # Assign to different users for variety
            owner = users[i % len(users)]
            
            print(f"  🔗 Creating connector: {connector_data['name']}")
            
            # Create web connector
            connector_name = f"sim_{connector_data['name'].lower().replace(' ', '_')}_{i}"
            full_url = f"{connector_data['base_url']}{connector_data['endpoint']}"
            
            web_connector_result = mindsdb_service.create_web_connector(
                connector_name=connector_name,
                base_url=connector_data["base_url"],
                endpoint=connector_data["endpoint"],
                method=connector_data["method"]
            )
            
            if web_connector_result.get("success"):
                print(f"    ✅ Web connector created: {connector_name}")
                
                # Create dataset view
                dataset_view_result = mindsdb_service.create_dataset_from_web_connector(
                    connector_name=connector_name,
                    dataset_name=connector_data["name"],
                    table_name="data"
                )
                
                if dataset_view_result.get("success"):
                    print(f"    ✅ Dataset view created: {dataset_view_result['view_name']}")
                    
                    # Create dataset record
                    dataset = Dataset(
                        name=connector_data["name"],
                        description=connector_data["description"],
                        type=DatasetType.JSON,
                        status=DatasetStatus.ACTIVE,
                        owner_id=owner.id,
                        organization_id=owner.organization_id,
                        sharing_level=connector_data["sharing_level"],
                        source_url=full_url,
                        connector_id=connector_name,
                        row_count=dataset_view_result.get("estimated_rows", random.randint(50, 500)),
                        column_count=len(dataset_view_result.get("columns", [])),
                        allow_download=True,
                        allow_api_access=True,
                        allow_ai_chat=True,
                        schema_info={
                            "columns": dataset_view_result.get("columns", []),
                            "sample_data": dataset_view_result.get("sample_data", [])
                        },
                        schema_metadata={
                            "data_source": "web_connector",
                            "api_endpoint": full_url,
                            "connector_name": connector_name,
                            "data_freshness": "real-time",
                            "created_at": datetime.utcnow().isoformat()
                        },
                        quality_metrics={
                            "overall_score": round(random.uniform(0.8, 1.0), 2),
                            "completeness": round(random.uniform(0.9, 1.0), 2),
                            "consistency": round(random.uniform(0.8, 0.95), 2),
                            "accuracy": round(random.uniform(0.85, 0.98), 2),
                            "issues": [],
                            "last_analyzed": datetime.utcnow().isoformat()
                        },
                        preview_data={
                            "headers": dataset_view_result.get("columns", []),
                            "sample_rows": dataset_view_result.get("sample_data", [])[:5],
                            "total_rows": dataset_view_result.get("estimated_rows", random.randint(50, 500)),
                            "is_sample": True,
                            "preview_generated_at": datetime.utcnow().isoformat()
                        }
                    )
                    
                    db.add(dataset)
                    db.commit()
                    db.refresh(dataset)
                    created_datasets.append(dataset)
                    
                    print(f"    ✅ Dataset created: ID {dataset.id} - Owner: {owner.email}")
                else:
                    print(f"    ❌ Failed to create dataset view: {dataset_view_result.get('error')}")
            else:
                print(f"    ❌ Failed to create web connector: {web_connector_result.get('error')}")
                
        except Exception as e:
            print(f"    ❌ Error creating connector {connector_data['name']}: {e}")
            continue
    
    return created_datasets

async def create_uploaded_datasets(db, generator, users):
    """Create mock uploaded datasets."""
    print("\n📁 Creating Uploaded Datasets...")
    created_datasets = []
    
    for i, dataset_data in enumerate(generator.uploaded_datasets):
        # Assign to different users for variety
        owner = users[i % len(users)]
        
        # Add some randomness to creation dates
        created_date = datetime.utcnow() - timedelta(days=random.randint(1, 30))
        
        dataset = Dataset(
            name=dataset_data["name"],
            description=dataset_data["description"],
            type=dataset_data["type"],
            status=DatasetStatus.ACTIVE,
            owner_id=owner.id,
            organization_id=owner.organization_id,
            sharing_level=dataset_data["sharing_level"],
            row_count=dataset_data["row_count"],
            column_count=dataset_data["column_count"],
            size_bytes=dataset_data["size_bytes"],
            allow_download=True,
            allow_api_access=True,
            allow_ai_chat=True,
            created_at=created_date,
            updated_at=created_date,
            schema_info={
                "columns": dataset_data["columns"],
                "sample_data": dataset_data["sample_data"]
            },
            schema_metadata={
                "data_source": "uploaded_file",
                "file_type": dataset_data["type"].value.lower(),
                "encoding": "utf-8",
                "columns": dataset_data["columns"],
                "data_types": {col: "string" for col in dataset_data["columns"]},  # Simplified for demo
                "created_at": created_date.isoformat()
            },
            quality_metrics={
                "overall_score": round(random.uniform(0.85, 0.98), 2),
                "completeness": round(random.uniform(0.92, 1.0), 2),
                "consistency": round(random.uniform(0.88, 0.96), 2),
                "accuracy": round(random.uniform(0.90, 0.99), 2),
                "issues": [],
                "last_analyzed": created_date.isoformat()
            },
            preview_data={
                "headers": dataset_data["columns"],
                "sample_rows": [list(row.values()) for row in dataset_data["sample_data"]],
                "total_rows": dataset_data["row_count"],
                "is_sample": True,
                "preview_generated_at": created_date.isoformat()
            }
        )
        
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        created_datasets.append(dataset)
        
        print(f"  ✅ Created: {dataset.name} - Owner: {owner.email} ({dataset.sharing_level.value})")
    
    return created_datasets

async def generate_simulation_summary(organizations, users, web_datasets, uploaded_datasets):
    """Generate a comprehensive summary of the simulation."""
    print("\n" + "="*80)
    print("🎯 COMPREHENSIVE SIMULATION SUMMARY")
    print("="*80)
    
    print(f"\n🏢 Organizations Created: {len(organizations)}")
    for org in organizations:
        org_users = [u for u in users if u.organization_id == org.id]
        print(f"  📋 {org.name}")
        print(f"      Users: {len(org_users)}")
        print(f"      Slug: {org.slug}")
    
    print(f"\n👥 Users Created: {len(users)}")
    for user in users:
        org_name = next((org.name for org in organizations if org.id == user.organization_id), "Unknown")
        print(f"  👤 {user.email} / {user.role}")
        print(f"      Name: {user.full_name}")
        print(f"      Organization: {org_name}")
        print(f"      Active: {user.is_active}")
    
    print(f"\n🌐 Web Connector Datasets: {len(web_datasets)}")
    for dataset in web_datasets:
        owner = next((u for u in users if u.id == dataset.owner_id), None)
        print(f"  📡 {dataset.name} (ID: {dataset.id})")
        print(f"      Owner: {owner.email if owner else 'Unknown'}")
        print(f"      Sharing: {dataset.sharing_level.value}")
        print(f"      Source: {dataset.source_url}")
        print(f"      Connector: {dataset.connector_id}")
    
    print(f"\n📁 Uploaded Datasets: {len(uploaded_datasets)}")
    for dataset in uploaded_datasets:
        owner = next((u for u in users if u.id == dataset.owner_id), None)
        print(f"  📊 {dataset.name} (ID: {dataset.id})")
        print(f"      Owner: {owner.email if owner else 'Unknown'}")
        print(f"      Sharing: {dataset.sharing_level.value}")
        print(f"      Type: {dataset.type.value}")
        print(f"      Rows: {dataset.row_count:,}")
    
    # Sharing level breakdown
    all_datasets = web_datasets + uploaded_datasets
    sharing_breakdown = {}
    for dataset in all_datasets:
        level = dataset.sharing_level.value
        sharing_breakdown[level] = sharing_breakdown.get(level, 0) + 1
    
    print(f"\n📊 Dataset Sharing Breakdown:")
    for level, count in sharing_breakdown.items():
        print(f"  🔒 {level.title()}: {count} datasets")
    
    print(f"\n🔧 Proxy Service Ports for Testing:")
    print(f"  🔌 MySQL Proxy: 10101")
    print(f"  🔌 PostgreSQL Proxy: 10102")
    print(f"  🔌 API Proxy: 10103")
    print(f"  🔌 ClickHouse Proxy: 10104")
    print(f"  🔌 MongoDB Proxy: 10105")
    print(f"  🔌 S3 Proxy: 10106")
    print(f"  🔌 Shared Links Proxy: 10107")
    
    print(f"\n🧪 Manual Testing Scenarios:")
    print(f"  1. Login with different users across organizations")
    print(f"  2. Test dataset visibility based on sharing levels")
    print(f"  3. Verify web connector real-time data access")
    print(f"  4. Test AI chat with different dataset types")
    print(f"  5. Verify proxy service connectivity")
    print(f"  6. Test cross-organization data sharing")
    
    print(f"\n📋 Test User Credentials:")
    for user in users:
        # Extract password from user data (this is for demo purposes)
        password = "tech2024" if "techcorp" in user.email else \
                  "data2024" if "datasci" in user.email else \
                  "startup2024" if "startuplab" in user.email else \
                  "research2024" if "research" in user.email else "demo123"
        print(f"  🔑 {user.email} / {password}")

async def main():
    """Main simulation function."""
    print("🚀 Starting Comprehensive Platform Simulation")
    print("=" * 60)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Initialize data generator
        generator = SimulationDataGenerator()
        
        # Initialize MindsDB service
        mindsdb_service = MindsDBService()
        
        # Create organizations
        organizations = await create_organizations(db, generator)
        
        # Create users
        users = await create_users(db, generator, organizations)
        
        # Create web connector datasets
        web_datasets = await create_web_connector_datasets(db, generator, users, mindsdb_service)
        
        # Create uploaded datasets
        uploaded_datasets = await create_uploaded_datasets(db, generator, users)
        
        # Generate summary
        await generate_simulation_summary(organizations, users, web_datasets, uploaded_datasets)
        
        print(f"\n✅ Simulation Complete!")
        print(f"   📊 Total Organizations: {len(organizations)}")
        print(f"   👥 Total Users: {len(users)}")
        print(f"   🌐 Web Connector Datasets: {len(web_datasets)}")
        print(f"   📁 Uploaded Datasets: {len(uploaded_datasets)}")
        print(f"   📋 Total Datasets: {len(web_datasets) + len(uploaded_datasets)}")
        
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())