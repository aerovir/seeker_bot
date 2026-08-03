"""Change events.short_description from String(1024) to Text.

Revision ID: 003
Revises: 002
Create Date: 2026-08-03

Описания событий достигают 3000 символов — String(1024) не вмещает
полное описание. Расширяем до Text (безлимит).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "events",
        "short_description",
        type_=sa.Text(),
        existing_type=sa.String(1024),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "events",
        "short_description",
        type_=sa.String(1024),
        existing_type=sa.Text(),
        existing_nullable=True,
    )
