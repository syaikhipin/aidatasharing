"""Add multi-file support to datasets

Revision ID: add_multi_file_support
Revises: previous
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_multi_file_support'
down_revision = 'previous'  # Replace with actual previous revision
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to datasets table
    op.add_column('datasets', sa.Column('is_multi_file_dataset', sa.Boolean(), default=False, nullable=False))
    op.add_column('datasets', sa.Column('primary_file_path', sa.String(), nullable=True))
    op.add_column('datasets', sa.Column('files_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('datasets', sa.Column('total_files_count', sa.Integer(), default=1, nullable=True))
    
    # Create dataset_files table
    op.create_table('dataset_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('relative_path', sa.String(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_type', sa.String(), nullable=True),
        sa.Column('mime_type', sa.String(), nullable=True),
        sa.Column('file_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_primary', sa.Boolean(), default=False, nullable=True),
        sa.Column('file_order', sa.Integer(), default=0, nullable=True),
        sa.Column('is_processed', sa.Boolean(), default=False, nullable=True),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dataset_files_id'), 'dataset_files', ['id'], unique=False)
    op.create_index(op.f('ix_dataset_files_dataset_id'), 'dataset_files', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_dataset_files_is_primary'), 'dataset_files', ['is_primary'], unique=False)
    op.create_index(op.f('ix_dataset_files_is_deleted'), 'dataset_files', ['is_deleted'], unique=False)


def downgrade():
    # Drop dataset_files table and indexes
    op.drop_index(op.f('ix_dataset_files_is_deleted'), table_name='dataset_files')
    op.drop_index(op.f('ix_dataset_files_is_primary'), table_name='dataset_files')
    op.drop_index(op.f('ix_dataset_files_dataset_id'), table_name='dataset_files')
    op.drop_index(op.f('ix_dataset_files_id'), table_name='dataset_files')
    op.drop_table('dataset_files')
    
    # Remove columns from datasets table
    op.drop_column('datasets', 'total_files_count')
    op.drop_column('datasets', 'files_metadata')
    op.drop_column('datasets', 'primary_file_path')
    op.drop_column('datasets', 'is_multi_file_dataset')