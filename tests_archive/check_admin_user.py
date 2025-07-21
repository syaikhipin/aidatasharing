#!/usr/bin/env python3
"""
Script to check and fix admin user privileges
"""

import sqlite3
import bcrypt
import os

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_and_fix_admin():
    """Check admin user status and fix if needed."""
    db_path = "./storage/aishare_platform.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        admin_email = "admin@example.com"
        admin_password = "admin123"
        
        print(f"Checking admin user: {admin_email}")
        
        # Check if admin user exists
        cursor.execute("SELECT id, email, full_name, is_active, is_superuser, role, organization_id FROM users WHERE email = ?", (admin_email,))
        admin_user = cursor.fetchone()
        
        if not admin_user:
            print("❌ Admin user not found! Creating...")
            
            # Get system admin organization
            cursor.execute("SELECT id FROM organizations WHERE slug = ?", ("system-admin",))
            admin_org = cursor.fetchone()
            org_id = admin_org[0] if admin_org else None
            
            # Create admin user
            hashed_password = hash_password(admin_password)
            cursor.execute("""
                INSERT INTO users (email, hashed_password, full_name, is_active, is_superuser, organization_id, role, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (admin_email, hashed_password, "Super Admin", True, True, org_id, "admin"))
            
            conn.commit()
            print("✅ Admin user created successfully!")
        else:
            user_id, email, full_name, is_active, is_superuser, role, org_id = admin_user
            print(f"✅ Admin user found: {email}")
            print(f"   - Full name: {full_name}")
            print(f"   - Is active: {bool(is_active)}")
            print(f"   - Is superuser: {bool(is_superuser)}")
            print(f"   - Role: {role}")
            print(f"   - Organization ID: {org_id}")
            
            # Fix admin user if needed
            needs_update = False
            updates = []
            
            if not is_superuser:
                print("⚠️  Admin user is not a superuser! Fixing...")
                updates.append("is_superuser = 1")
                needs_update = True
            
            if not is_active:
                print("⚠️  Admin user is not active! Fixing...")
                updates.append("is_active = 1")
                needs_update = True
            
            if role != "admin":
                print("⚠️  Admin user role is not 'admin'! Fixing...")
                updates.append("role = 'admin'")
                needs_update = True
            
            if needs_update:
                update_query = f"UPDATE users SET {', '.join(updates)}, updated_at = datetime('now') WHERE id = ?"
                cursor.execute(update_query, (user_id,))
                conn.commit()
                print("✅ Admin user updated successfully!")
            else:
                print("✅ Admin user is properly configured!")
        
        # Check all users
        print("\n📋 All users in database:")
        cursor.execute("SELECT email, is_superuser, is_active, role FROM users")
        users = cursor.fetchall()
        for email, is_superuser, is_active, role in users:
            print(f"   - {email} (superuser: {bool(is_superuser)}, active: {bool(is_active)}, role: {role})")
        
        # Check organizations
        print("\n🏢 Organizations in database:")
        cursor.execute("SELECT name, slug FROM organizations")
        orgs = cursor.fetchall()
        for name, slug in orgs:
            print(f"   - {name} ({slug})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    check_and_fix_admin()