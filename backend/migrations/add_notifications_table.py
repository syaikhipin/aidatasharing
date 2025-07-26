"""
Add notifications table

This migration adds the notifications table to support user notifications
for data access requests and other system events.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from app.core.database import engine
from datetime import datetime

Base = declarative_base()

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String, default="info")  # info, warning, error, success
    is_read = Column(Boolean, default=False)
    related_resource_type = Column(String, nullable=True)  # dataset, model, etc.
    related_resource_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)

def upgrade():
    """Create the notifications table"""
    try:
        Notification.__table__.create(engine, checkfirst=True)
        print("✅ Notifications table created successfully")
    except Exception as e:
        print(f"❌ Error creating notifications table: {e}")

def downgrade():
    """Drop the notifications table"""
    try:
        Notification.__table__.drop(engine, checkfirst=True)
        print("✅ Notifications table dropped successfully")
    except Exception as e:
        print(f"❌ Error dropping notifications table: {e}")

if __name__ == "__main__":
    print("🔧 Running notifications migration...")
    upgrade()