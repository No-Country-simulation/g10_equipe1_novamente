"""Add course generation ID

Revision ID: 13cda7f04a52
Revises: 7cbad33f4a0e
"""

import sqlalchemy as sa
from alembic import op

revision = "13cda7f04a52"
down_revision = "7cbad33f4a0e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("course", sa.Column("generation_id", sa.Uuid(), nullable=True))


def downgrade() -> None:
    op.drop_column("course", "generation_id")
