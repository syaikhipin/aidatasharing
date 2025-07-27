#!/usr/bin/env python3
"""
Migration: Add admin configuration tables
Created: 2025-07-27T01:45:00
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)

def upgrade(cursor):
    """Apply the migration - Add admin configuration tables"""
    
    # Create configuration_overrides table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuration_overrides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key VARCHAR(255) UNIQUE NOT NULL,
            category VARCHAR(50) NOT NULL DEFAULT 'system',
            config_type VARCHAR(50) NOT NULL DEFAULT 'string',
            value TEXT,
            default_value TEXT,
            env_var_name VARCHAR(255),
            title VARCHAR(255) NOT NULL,
            description TEXT,
            is_sensitive BOOLEAN DEFAULT 0,
            is_required BOOLEAN DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            requires_restart BOOLEAN DEFAULT 0,
            validation_regex VARCHAR(500),
            min_value INTEGER,
            max_value INTEGER,
            allowed_values TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_applied_at TIMESTAMP
        )
    ''')
    
    # Create indexes for configuration_overrides
    cursor.execute('CREATE INDEX IF NOT EXISTS ix_configuration_overrides_id ON configuration_overrides (id)')
    cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS ix_configuration_overrides_key ON configuration_overrides (key)')
    
    # Create mindsdb_configurations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mindsdb_configurations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_name VARCHAR(100) NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            mindsdb_url VARCHAR(500) NOT NULL,
            mindsdb_database VARCHAR(100) DEFAULT 'mindsdb',
            mindsdb_username VARCHAR(100),
            mindsdb_password VARCHAR(255),
            permanent_storage_config TEXT,
            ai_engines_config TEXT,
            file_upload_config TEXT,
            custom_config TEXT,
            last_health_check TIMESTAMP,
            is_healthy BOOLEAN DEFAULT 0,
            health_status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create index for mindsdb_configurations
    cursor.execute('CREATE INDEX IF NOT EXISTS ix_mindsdb_configurations_id ON mindsdb_configurations (id)')
    
    # Create configuration_history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuration_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key VARCHAR(255) NOT NULL,
            config_type VARCHAR(50) NOT NULL,
            old_value TEXT,
            new_value TEXT,
            change_reason TEXT,
            changed_by_user_id INTEGER,
            changed_by_email VARCHAR(255),
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            applied_successfully BOOLEAN,
            application_error TEXT,
            applied_at TIMESTAMP
        )
    ''')
    
    # Create index for configuration_history
    cursor.execute('CREATE INDEX IF NOT EXISTS ix_configuration_history_id ON configuration_history (id)')
    
    logger.info("Admin configuration tables created successfully")

def downgrade(cursor):
    """Rollback the migration"""
    cursor.execute('DROP TABLE IF EXISTS configuration_history')
    cursor.execute('DROP TABLE IF EXISTS mindsdb_configurations')
    cursor.execute('DROP TABLE IF EXISTS configuration_overrides')
    logger.info("Admin configuration tables dropped successfully")