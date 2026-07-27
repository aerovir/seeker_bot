"""Initial schema — all core tables.

Revision ID: 001
Revises:
Create Date: 2026-07-27

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Users ---
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(128), nullable=True),
        sa.Column("first_name", sa.String(256), nullable=True),
        sa.Column("last_name", sa.String(256), nullable=True),
        sa.Column("language_code", sa.String(8), nullable=False, server_default="ru"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "notification_frequency",
            sa.Enum("REALTIME", "DIGEST_DAILY", "DIGEST_WEEKLY", "NONE", name="notificationfrequency"),
            nullable=False,
            server_default="DIGEST_DAILY",
        ),
        sa.Column("last_digest_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    # --- Cities ---
    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("name_ru", sa.String(128), nullable=False),
        sa.Column("name_en", sa.String(128), nullable=False),
        sa.Column("name_ru_prepositional", sa.String(128), nullable=False, server_default=""),
        sa.Column("name_ru_genitive", sa.String(128), nullable=False, server_default=""),
        sa.Column("region", sa.String(128), nullable=True),
        sa.Column("country", sa.String(64), nullable=False, server_default="Россия"),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="Europe/Moscow"),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("aliases", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cities_slug", "cities", ["slug"], unique=True)

    # --- Categories ---
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("name_ru", sa.String(128), nullable=False),
        sa.Column("name_en", sa.String(128), nullable=False),
        sa.Column("emoji", sa.String(8), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("keywords", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)

    # --- Content Sources ---
    op.create_table(
        "content_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column(
            "source_type",
            sa.Enum("RSS", "WEB_SCRAPE", "API", name="sourcetype"),
            nullable=False,
        ),
        sa.Column("feed_url", sa.String(2048), nullable=False),
        sa.Column("base_url", sa.String(2048), nullable=True),
        sa.Column("config", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("fetch_interval_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("default_city_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "PAUSED", "ERROR", "DISABLED", name="sourcestatus"),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("consecutive_errors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["default_city_id"], ["cities.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_content_sources_slug", "content_sources", ["slug"], unique=True)
    op.create_index("ix_content_sources_status", "content_sources", ["status"])

    # --- Events ---
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(256), nullable=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("short_description", sa.String(1024), nullable=True),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("image_url", sa.String(2048), nullable=True),
        sa.Column("image_data", postgresql.JSON(), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_multiday", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("venue_name", sa.String(512), nullable=True),
        sa.Column("venue_address", sa.String(512), nullable=True),
        sa.Column("price_min", sa.Float(), nullable=True),
        sa.Column("price_max", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(8), nullable=False, server_default="RUB"),
        sa.Column("ticket_url", sa.String(2048), nullable=True),
        sa.Column("ticket_provider", sa.String(64), nullable=True),
        sa.Column(
            "status",
            sa.Enum("PENDING", "PUBLISHED", "ARCHIVED", "REJECTED", name="eventstatus"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("source_url", sa.String(2048), nullable=True),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_data", postgresql.JSON(), nullable=True),
        sa.Column("enrichment_data", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["source_id"], ["content_sources.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_events_title", "events", ["title"])
    op.create_index("ix_events_event_type", "events", ["event_type"])
    op.create_index("ix_events_start_date", "events", ["start_date"])
    op.create_index("ix_events_status", "events", ["status"])
    op.create_index("ix_events_is_featured", "events", ["is_featured"])
    op.create_index("ix_events_external_id", "events", ["external_id"], unique=True)
    op.create_index(
        "ix_events_feed_query",
        "events",
        ["start_date", "status", "is_featured"],
        postgresql_where=sa.text("status = 'PUBLISHED'"),
    )

    # --- Event-Category assignments ---
    op.create_table(
        "event_category_assignments",
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("method", sa.String(32), nullable=False, server_default="keyword"),
        sa.PrimaryKeyConstraint("event_id", "category_id"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
    )

    # --- Event-City assignments ---
    op.create_table(
        "event_city_assignments",
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("method", sa.String(32), nullable=False, server_default="gazetteer"),
        sa.PrimaryKeyConstraint("event_id", "city_id"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
    )

    # --- User-City preferences ---
    op.create_table(
        "user_city_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
    )

    # --- User-Category preferences ---
    op.create_table(
        "user_category_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
    )

    # --- Source items (dedup tracker) ---
    op.create_table(
        "source_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("item_guid", sa.String(512), nullable=False),
        sa.Column("item_hash", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["source_id"], ["content_sources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("source_id", "item_guid", name="uq_source_item"),
    )
    op.create_index("ix_source_items_source_id", "source_items", ["source_id"])

    # --- Source default categories (many-to-many) ---
    op.create_table(
        "source_default_categories",
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("source_id", "category_id"),
        sa.ForeignKeyConstraint(["source_id"], ["content_sources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
    )

    # --- Notification log ---
    op.create_table(
        "notification_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column(
            "notification_type",
            sa.Enum("DIGEST", "BREAKING", "TEST", name="notificationtype"),
            nullable=False,
            server_default="DIGEST",
        ),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("was_delivered", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_notification_log_user_id", "notification_log", ["user_id"])


def downgrade() -> None:
    op.drop_table("notification_log")
    op.drop_table("source_default_categories")
    op.drop_table("source_items")
    op.drop_table("user_category_preferences")
    op.drop_table("user_city_preferences")
    op.drop_table("event_city_assignments")
    op.drop_table("event_category_assignments")
    op.drop_table("events")
    op.drop_table("content_sources")
    op.drop_table("categories")
    op.drop_table("cities")
    op.drop_table("users")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS notificationfrequency")
    op.execute("DROP TYPE IF EXISTS sourcetype")
    op.execute("DROP TYPE IF EXISTS sourcestatus")
    op.execute("DROP TYPE IF EXISTS eventstatus")
    op.execute("DROP TYPE IF EXISTS notificationtype")
