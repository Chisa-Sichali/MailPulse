from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MailboxCreateRequest(BaseModel):
    email_address: EmailStr
    password: str = Field(min_length=1, max_length=512)
    imap_host: str = Field(min_length=1, max_length=255)
    imap_port: int = Field(default=993, ge=1, le=65535)
    imap_username: EmailStr | None = None
    is_enabled: bool = True


class MailboxUpdateRequest(BaseModel):
    email_address: EmailStr | None = None
    password: str | None = Field(default=None, min_length=1, max_length=512)
    imap_host: str | None = Field(default=None, min_length=1, max_length=255)
    imap_port: int | None = Field(default=None, ge=1, le=65535)
    imap_username: EmailStr | None = None
    is_enabled: bool | None = None


class MailboxResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email_address: EmailStr
    imap_username: EmailStr
    imap_host: str
    imap_port: int
    is_enabled: bool
    health_status: str
    last_sync_at: datetime | None
    last_error_at: datetime | None
    last_error_message: str | None
    created_at: datetime
    updated_at: datetime


class MailboxConnectionTestResponse(BaseModel):
    success: bool
    message: str
    health_status: str
    mailbox: MailboxResponse


class MailboxListResponse(BaseModel):
    items: list[MailboxResponse]
    limit: int
    offset: int
