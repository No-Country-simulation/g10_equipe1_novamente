"""Remove is_superuser from User

Revision ID: b7c4e1f2a9d3
Revises: fe56fa70289e
Create Date: 2026-10-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7c4e1f2a9d3'
down_revision = 'fe56fa70289e'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('user', 'is_superuser')


def downgrade():
    op.add_column('user', sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.false()))
