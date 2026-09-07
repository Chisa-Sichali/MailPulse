from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EmailEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    mailbox_id: UUID
    message_id: str
    imap_uid: str | None
    sender_email: str
    sender_name: str
    recipients: list[str]
    subject: str
    text_body: str
    html_body: str
    attachments_metadata: list[dict]
    in_reply_to: str | None
    status: str
    error_message: str | None
    attempt_count: int
    received_at: datetime | None
    processed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class EmailEventListResponse(BaseModel):
    items: list[EmailEventResponse]
    limit: int
    offset: int
    total: int


class MonitorSweepResponse(BaseModel):
    status: str
    job_id: str | None = None
