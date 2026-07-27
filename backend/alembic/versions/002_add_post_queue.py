"""Add post_queue table for channel publishing.

Revision ID: 002
Revises: 001
Create Date: 2026-07-27

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "post_queue",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("channel_id", sa.String(128), nullable=False, server_default=""),
        sa.Column(
            "status",
            sa.Enum("PENDING", "SCHEDULED", "PUBLISHED", "SKIPPED", name="poststatus"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("channel_message_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_post_queue_event_id", "post_queue", ["event_id"])
    op.create_index("ix_post_queue_status", "post_queue", ["status"])


def downgrade() -> None:
    op.drop_index("ix_post_queue_status")
    op.drop_index("ix_post_queue_event_id")
    op.drop_table("post_queue")
    op.execute("DROP TYPE IF EXISTS poststatus")
