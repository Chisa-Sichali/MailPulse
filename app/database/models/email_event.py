import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database.models import Base

class EmailEventStatus(str, enum.Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"

class EmailEvent(Base):
    __tablename__ = "email_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mailbox_id = Column(UUID(as_uuid=True), ForeignKey("mailboxes.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(String(512), nullable=False)
    imap_uid = Column(String(64), nullable=True)
    sender_email = Column(String(255), nullable=False)
    sender_name = Column(String(255), nullable=False, server_default=text("''"))
    recipients = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    subject = Column(Text, nullable=False, server_default=text("''"))
    text_body = Column(Text, nullable=False, server_default=text("''"))
    html_body = Column(Text, nullable=False, server_default=text("''"))
    attachments_metadata = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    in_reply_to = Column(String(512), nullable=True)
    status = Column(String(32), nullable=False, server_default=text("'pending'"))
    error_message = Column(Text, nullable=True)
    attempt_count = Column(Integer, nullable=False, server_default=text("0"))
    received_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), onupdate=datetime.utcnow)

    mailbox = relationship("Mailbox", back_populates="email_events")
    webhook_deliveries = relationship("WebhookDelivery", back_populates="email_event", cascade="all, delete-orphan")
