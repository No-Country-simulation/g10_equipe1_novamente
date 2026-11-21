"""add course object cleanup

Revision ID: 7cbad33f4a0e
Revises: b23eaa5c1998
"""

import sqlalchemy as sa
from alembic import op

revision = "7cbad33f4a0e"
down_revision = "b23eaa5c1998"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "course_object_cleanup",
        sa.Column("course_id", sa.Uuid(), primary_key=True),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("course_object_cleanup")
