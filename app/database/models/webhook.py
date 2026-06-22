import enum
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database.models import Base

class WebhookDeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"

class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(2048), nullable=False)
    name = Column(String(255), nullable=True)
    encrypted_secret = Column(Text, nullable=False)
    secret_prefix = Column(String(16), nullable=False)
    is_enabled = Column(Boolean, nullable=False, server_default=text("true"))
    event_types = Column(JSONB, nullable=False, server_default=text("'[\"email.received\"]'::jsonb"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    user = relationship("User", back_populates="webhooks")
    webhook_deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")

class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    webhook_id = Column(UUID(as_uuid=True), ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False)
    email_event_id = Column(UUID(as_uuid=True), ForeignKey("email_events.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(32), nullable=False, server_default=text("'pending'"))
    attempt_count = Column(Integer, nullable=False, server_default=text("0"))
    http_status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), onupdate=datetime.utcnow)

    webhook = relationship("Webhook", back_populates="webhook_deliveries")
    email_event = relationship("EmailEvent", back_populates="webhook_deliveries")
