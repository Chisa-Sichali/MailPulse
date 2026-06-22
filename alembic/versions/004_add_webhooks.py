"""Add webhooks and webhook_deliveries tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_add_webhooks"
down_revision: Union[str, None] = "003_add_email_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "webhooks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("encrypted_secret", sa.Text(), nullable=False),
        sa.Column("secret_prefix", sa.String(length=16), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "event_types",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[\"email.received\"]'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_webhooks_user_id_active",
        "webhooks",
        ["user_id", "deleted_at"],
        unique=False,
    )
    op.create_index("ix_webhooks_deleted_at", "webhooks", ["deleted_at"], unique=False)

    op.create_table(
        "webhook_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("webhook_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("http_status_code", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["email_event_id"], ["email_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["webhook_id"], ["webhooks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_webhook_deliveries_webhook_event",
        "webhook_deliveries",
        ["webhook_id", "email_event_id"],
        unique=True,
    )
    op.create_index(
        "ix_webhook_deliveries_status_retry",
        "webhook_deliveries",
        ["status", "next_retry_at"],
        unique=False,
    )
    op.create_index(
        "ix_webhook_deliveries_email_event_id",
        "webhook_deliveries",
        ["email_event_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_webhook_deliveries_email_event_id", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_deliveries_status_retry", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_deliveries_webhook_event", table_name="webhook_deliveries")
    op.drop_table("webhook_deliveries")
    op.drop_index("ix_webhooks_deleted_at", table_name="webhooks")
    op.drop_index("ix_webhooks_user_id_active", table_name="webhooks")
    op.drop_table("webhooks")
