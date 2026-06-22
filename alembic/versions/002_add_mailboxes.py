"""Add mailboxes table for user-managed IMAP inboxes."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_add_mailboxes"
down_revision: Union[str, None] = "001_initial_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mailboxes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email_address", sa.String(length=255), nullable=False),
        sa.Column("imap_username", sa.String(length=255), nullable=False),
        sa.Column("imap_host", sa.String(length=255), nullable=False),
        sa.Column("imap_port", sa.Integer(), nullable=False, server_default=sa.text("993")),
        sa.Column("encrypted_password", sa.Text(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "health_status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'unknown'"),
        ),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
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
        "ix_mailboxes_user_id_active",
        "mailboxes",
        ["user_id", "deleted_at"],
        unique=False,
    )
    op.create_index(
        "ix_mailboxes_enabled_health",
        "mailboxes",
        ["is_enabled", "health_status"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_mailboxes_email_active",
        "mailboxes",
        ["user_id", "email_address"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_mailboxes_deleted_at", "mailboxes", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_mailboxes_deleted_at", table_name="mailboxes")
    op.drop_index("ix_mailboxes_email_active", table_name="mailboxes")
    op.drop_index("ix_mailboxes_enabled_health", table_name="mailboxes")
    op.drop_index("ix_mailboxes_user_id_active", table_name="mailboxes")
    op.drop_table("mailboxes")
