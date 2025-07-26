"""Add mindsdb_storage_path to file_uploads table

Revision ID: add_permanent_storage_path
Revises: previous_revision
Create Date: 2024-07-26 23:13:50.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_permanent_storage_path'
down_revision = None  # Update this with the actual previous revision
branch_labels = None
depends_on = None


def upgrade():
    """Add mindsdb_storage_path column to file_uploads table"""
    # Add the new column
    op.add_column('file_uploads', sa.Column('mindsdb_storage_path', sa.String(500), nullable=True))


def downgrade():
    """Remove mindsdb_storage_path column from file_uploads table"""
    # Remove the column
    op.drop_column('file_uploads', 'mindsdb_storage_path')