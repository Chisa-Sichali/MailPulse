"""Add email_events table for processed inbox messages."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_add_email_events"
down_revision: Union[str, None] = "002_add_mailboxes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mailbox_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", sa.String(length=512), nullable=False),
        sa.Column("imap_uid", sa.String(length=64), nullable=True),
        sa.Column("sender_email", sa.String(length=255), nullable=False),
        sa.Column("sender_name", sa.String(length=255), nullable=False, server_default=sa.text("''")),
        sa.Column("recipients", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("subject", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("text_body", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("html_body", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column(
            "attachments_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("in_reply_to", sa.String(length=512), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_email_events_mailbox_message_id",
        "email_events",
        ["mailbox_id", "message_id"],
        unique=True,
    )
    op.create_index(
        "ix_email_events_mailbox_created_at",
        "email_events",
        ["mailbox_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_email_events_status_created_at",
        "email_events",
        ["status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_email_events_status_created_at", table_name="email_events")
    op.drop_index("ix_email_events_mailbox_created_at", table_name="email_events")
    op.drop_index("ix_email_events_mailbox_message_id", table_name="email_events")
    op.drop_table("email_events")
