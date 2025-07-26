"""Add enhanced configuration management tables

Revision ID: add_admin_config_tables
Revises: add_permanent_storage_path
Create Date: 2024-07-26 23:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision = 'add_admin_config_tables'
down_revision = 'add_permanent_storage_path'
branch_labels = None
depends_on = None


def upgrade():
    """Add enhanced configuration management tables"""
    
    # Create configuration_overrides table
    op.create_table('configuration_overrides',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('config_type', sa.String(length=50), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('default_value', sa.Text(), nullable=True),
        sa.Column('env_var_name', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_sensitive', sa.Boolean(), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('requires_restart', sa.Boolean(), nullable=True),
        sa.Column('validation_regex', sa.String(length=500), nullable=True),
        sa.Column('min_value', sa.Integer(), nullable=True),
        sa.Column('max_value', sa.Integer(), nullable=True),
        sa.Column('allowed_values', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_applied_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_configuration_overrides_id'), 'configuration_overrides', ['id'], unique=False)
    op.create_index(op.f('ix_configuration_overrides_key'), 'configuration_overrides', ['key'], unique=True)

    # Create mindsdb_configurations table
    op.create_table('mindsdb_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('mindsdb_url', sa.String(length=500), nullable=False),
        sa.Column('mindsdb_database', sa.String(length=100), nullable=True),
        sa.Column('mindsdb_username', sa.String(length=100), nullable=True),
        sa.Column('mindsdb_password', sa.String(length=255), nullable=True),
        sa.Column('permanent_storage_config', sa.JSON(), nullable=True),
        sa.Column('ai_engines_config', sa.JSON(), nullable=True),
        sa.Column('file_upload_config', sa.JSON(), nullable=True),
        sa.Column('custom_config', sa.JSON(), nullable=True),
        sa.Column('last_health_check', sa.DateTime(), nullable=True),
        sa.Column('is_healthy', sa.Boolean(), nullable=True),
        sa.Column('health_status', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mindsdb_configurations_id'), 'mindsdb_configurations', ['id'], unique=False)

    # Create configuration_history table
    op.create_table('configuration_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_key', sa.String(length=255), nullable=False),
        sa.Column('config_type', sa.String(length=50), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('changed_by_user_id', sa.Integer(), nullable=True),
        sa.Column('changed_by_email', sa.String(length=255), nullable=True),
        sa.Column('changed_at', sa.DateTime(), nullable=True),
        sa.Column('applied_successfully', sa.Boolean(), nullable=True),
        sa.Column('application_error', sa.Text(), nullable=True),
        sa.Column('applied_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_configuration_history_id'), 'configuration_history', ['id'], unique=False)


def downgrade():
    """Remove enhanced configuration management tables"""
    op.drop_index(op.f('ix_configuration_history_id'), table_name='configuration_history')
    op.drop_table('configuration_history')
    op.drop_index(op.f('ix_mindsdb_configurations_id'), table_name='mindsdb_configurations')
    op.drop_table('mindsdb_configurations')
    op.drop_index(op.f('ix_configuration_overrides_key'), table_name='configuration_overrides')
    op.drop_index(op.f('ix_configuration_overrides_id'), table_name='configuration_overrides')
    op.drop_table('configuration_overrides')