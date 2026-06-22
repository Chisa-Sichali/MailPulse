import uuid
from typing import Sequence, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.email_event import EmailEvent, EmailEventStatus
from app.database.models.mailbox import Mailbox

class EmailEventRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_message_id(self, mailbox_id: uuid.UUID, message_id: str) -> Optional[EmailEvent]:
        stmt = select(EmailEvent).where(EmailEvent.mailbox_id == mailbox_id, EmailEvent.message_id == message_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, event_id: uuid.UUID) -> Optional[EmailEvent]:
        stmt = select(EmailEvent).where(EmailEvent.id == event_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_for_user(self, event_id: uuid.UUID, user_id: uuid.UUID) -> Optional[EmailEvent]:
        stmt = select(EmailEvent).join(Mailbox).where(EmailEvent.id == event_id, Mailbox.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID, mailbox_id: Optional[uuid.UUID] = None, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> Sequence[EmailEvent]:
        stmt = select(EmailEvent).join(Mailbox).where(Mailbox.user_id == user_id).order_by(EmailEvent.created_at.desc())
        if mailbox_id:
            stmt = stmt.where(EmailEvent.mailbox_id == mailbox_id)
        if status:
            stmt = stmt.where(EmailEvent.status == status)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create_from_parsed(self, mailbox_id: uuid.UUID, message_id: str, imap_uid: Optional[str], sender_email: str, sender_name: str, recipients: list, subject: str, text_body: str, html_body: str, attachments_metadata: list, in_reply_to: Optional[str], received_at: Optional[datetime]) -> EmailEvent:
        event = EmailEvent(
            mailbox_id=mailbox_id,
            message_id=message_id,
            imap_uid=imap_uid,
            sender_email=sender_email,
            sender_name=sender_name,
            recipients=recipients,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            attachments_metadata=attachments_metadata,
            in_reply_to=in_reply_to,
            received_at=received_at
        )
        self._session.add(event)
        await self._session.commit()
        await self._session.refresh(event)
        return event

    async def mark_processed(self, event: EmailEvent) -> None:
        event.processed_at = datetime.utcnow()
        self._session.add(event)
        await self._session.commit()

    async def mark_pending_retry(self, event: EmailEvent) -> None:
        event.status = EmailEventStatus.PENDING.value
        event.attempt_count += 1
        self._session.add(event)
        await self._session.commit()
