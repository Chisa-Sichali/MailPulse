import enum
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.models import Base

class MailboxHealthStatus(str, enum.Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    ERROR = "error"
    UNKNOWN = "unknown"

class Mailbox(Base):
    __tablename__ = "mailboxes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    email_address = Column(String(255), nullable=False)
    imap_username = Column(String(255), nullable=False)
    imap_host = Column(String(255), nullable=False)
    imap_port = Column(Integer, nullable=False, server_default=text("993"))
    encrypted_password = Column(Text, nullable=False)
    is_enabled = Column(Boolean, nullable=False, server_default=text("true"))
    health_status = Column(String(32), nullable=False, server_default=text("'unknown'"))
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_error_at = Column(DateTime(timezone=True), nullable=True)
    last_error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    user = relationship("User", back_populates="mailboxes")
    email_events = relationship("EmailEvent", back_populates="mailbox", cascade="all, delete-orphan")
