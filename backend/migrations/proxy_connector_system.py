"""
Database migration for Secure Proxy Connector System
Creates tables for proxy connectors, shared links, access logs, and credential vault
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'proxy_connector_system'
down_revision = 'previous_migration'  # Replace with actual previous migration
branch_labels = None
depends_on = None


def upgrade():
    # Create proxy_connectors table
    op.create_table(
        'proxy_connectors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('proxy_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('connector_type', sa.String(50), nullable=False),
        sa.Column('proxy_url', sa.String(500), nullable=False),
        sa.Column('access_token', sa.String(255), nullable=False),
        sa.Column('real_connection_config', sa.JSON(), nullable=True),
        sa.Column('real_credentials', sa.JSON(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True, default=False),
        sa.Column('allowed_operations', sa.JSON(), nullable=True),
        sa.Column('rate_limit', sa.Integer(), nullable=True, default=100),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('total_requests', sa.Integer(), nullable=True, default=0),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for proxy_connectors
    op.create_index('idx_proxy_connectors_proxy_id', 'proxy_connectors', ['proxy_id'], unique=True)
    op.create_index('idx_proxy_connectors_organization_id', 'proxy_connectors', ['organization_id'])
    op.create_index('idx_proxy_connectors_access_token', 'proxy_connectors', ['access_token'], unique=True)
    op.create_index('idx_proxy_connectors_created_by', 'proxy_connectors', ['created_by'])

    # Create shared_proxy_links table
    op.create_table(
        'shared_proxy_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('share_id', sa.String(255), nullable=False),
        sa.Column('proxy_connector_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('public_url', sa.String(500), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=True, default=False),
        sa.Column('requires_authentication', sa.Boolean(), nullable=True, default=True),
        sa.Column('allowed_users', sa.JSON(), nullable=True),
        sa.Column('allowed_domains', sa.JSON(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('current_uses', sa.Integer(), nullable=True, default=0),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['proxy_connector_id'], ['proxy_connectors.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for shared_proxy_links
    op.create_index('idx_shared_proxy_links_share_id', 'shared_proxy_links', ['share_id'], unique=True)
    op.create_index('idx_shared_proxy_links_proxy_connector_id', 'shared_proxy_links', ['proxy_connector_id'])
    op.create_index('idx_shared_proxy_links_created_by', 'shared_proxy_links', ['created_by'])
    op.create_index('idx_shared_proxy_links_expires_at', 'shared_proxy_links', ['expires_at'])

    # Create proxy_access_logs table
    op.create_table(
        'proxy_access_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('proxy_connector_id', sa.Integer(), nullable=False),
        sa.Column('shared_link_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_ip', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('operation_type', sa.String(100), nullable=True),
        sa.Column('operation_details', sa.JSON(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response_size', sa.Integer(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('accessed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['proxy_connector_id'], ['proxy_connectors.id'], ),
        sa.ForeignKeyConstraint(['shared_link_id'], ['shared_proxy_links.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for proxy_access_logs
    op.create_index('idx_proxy_access_logs_proxy_connector_id', 'proxy_access_logs', ['proxy_connector_id'])
    op.create_index('idx_proxy_access_logs_shared_link_id', 'proxy_access_logs', ['shared_link_id'])
    op.create_index('idx_proxy_access_logs_user_id', 'proxy_access_logs', ['user_id'])
    op.create_index('idx_proxy_access_logs_accessed_at', 'proxy_access_logs', ['accessed_at'])
    op.create_index('idx_proxy_access_logs_operation_type', 'proxy_access_logs', ['operation_type'])

    # Create proxy_credential_vault table
    op.create_table(
        'proxy_credential_vault',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vault_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('credential_type', sa.String(50), nullable=False),
        sa.Column('encrypted_credentials', sa.Text(), nullable=False),
        sa.Column('encryption_key_id', sa.String(255), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True, default=0),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for proxy_credential_vault
    op.create_index('idx_proxy_credential_vault_vault_id', 'proxy_credential_vault', ['vault_id'], unique=True)
    op.create_index('idx_proxy_credential_vault_organization_id', 'proxy_credential_vault', ['organization_id'])
    op.create_index('idx_proxy_credential_vault_created_by', 'proxy_credential_vault', ['created_by'])
    op.create_index('idx_proxy_credential_vault_credential_type', 'proxy_credential_vault', ['credential_type'])


def downgrade():
    # Drop tables in reverse order to handle foreign key constraints
    op.drop_table('proxy_credential_vault')
    op.drop_table('proxy_access_logs')
    op.drop_table('shared_proxy_links')
    op.drop_table('proxy_connectors')


# Additional helper functions for data migration if needed
def migrate_existing_connectors():
    """
    Optional: Migrate existing connectors to proxy format
    This function can be called separately if you want to convert
    existing connectors to the new proxy system
    """
    pass


def create_default_proxy_settings():
    """
    Optional: Create default proxy settings and configurations
    """
    pass


# Performance optimization queries
def create_additional_indexes():
    """
    Create additional indexes for performance optimization
    """
    # Composite indexes for common query patterns
    op.create_index(
        'idx_proxy_connectors_org_type_active',
        'proxy_connectors',
        ['organization_id', 'connector_type', 'is_active']
    )
    
    op.create_index(
        'idx_shared_links_public_active_expires',
        'shared_proxy_links',
        ['is_public', 'is_active', 'expires_at']
    )
    
    op.create_index(
        'idx_access_logs_connector_time',
        'proxy_access_logs',
        ['proxy_connector_id', 'accessed_at']
    )


def create_triggers():
    """
    Create database triggers for automatic updates
    """
    # Trigger to update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Apply trigger to relevant tables
    for table in ['proxy_connectors', 'shared_proxy_links', 'proxy_credential_vault']:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def create_views():
    """
    Create database views for common queries
    """
    # View for active proxy connectors with usage stats
    op.execute("""
        CREATE VIEW active_proxy_connectors AS
        SELECT 
            pc.*,
            COUNT(pal.id) as recent_requests,
            MAX(pal.accessed_at) as last_request_at
        FROM proxy_connectors pc
        LEFT JOIN proxy_access_logs pal ON pc.id = pal.proxy_connector_id
            AND pal.accessed_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
        WHERE pc.is_active = true
        GROUP BY pc.id;
    """)
    
    # View for shared link analytics
    op.execute("""
        CREATE VIEW shared_link_analytics AS
        SELECT 
            spl.*,
            COUNT(pal.id) as total_accesses,
            COUNT(DISTINCT pal.user_id) as unique_users,
            AVG(pal.execution_time_ms) as avg_response_time
        FROM shared_proxy_links spl
        LEFT JOIN proxy_access_logs pal ON spl.id = pal.shared_link_id
        WHERE spl.is_active = true
        GROUP BY spl.id;
    """)


# Security functions
def create_security_policies():
    """
    Create row-level security policies if using PostgreSQL RLS
    """
    # Enable RLS on sensitive tables
    for table in ['proxy_connectors', 'shared_proxy_links', 'proxy_credential_vault']:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
    
    # Create policies for organization isolation
    op.execute("""
        CREATE POLICY proxy_connectors_org_isolation ON proxy_connectors
        FOR ALL TO authenticated_users
        USING (organization_id = current_setting('app.current_organization_id')::integer);
    """)


if __name__ == "__main__":
    # This allows running the migration script directly for testing
    print("Proxy Connector System Migration")
    print("This migration creates tables for:")
    print("- Proxy Connectors")
    print("- Shared Proxy Links") 
    print("- Access Logs")
    print("- Credential Vault")
    print("\nRun with: alembic upgrade head")