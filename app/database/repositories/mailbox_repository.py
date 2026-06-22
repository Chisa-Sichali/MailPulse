import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.mailbox import Mailbox

class MailboxRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, mailbox_id: uuid.UUID) -> Optional[Mailbox]:
        stmt = select(Mailbox).where(Mailbox.id == mailbox_id, Mailbox.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_by_id_for_user(self, mailbox_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Mailbox]:
        stmt = select(Mailbox).where(Mailbox.id == mailbox_id, Mailbox.user_id == user_id, Mailbox.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID) -> Sequence[Mailbox]:
        stmt = select(Mailbox).where(Mailbox.user_id == user_id, Mailbox.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_enabled(self) -> Sequence[Mailbox]:
        stmt = select(Mailbox).where(Mailbox.is_enabled.is_(True), Mailbox.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        email_address: str,
        imap_username: str,
        imap_host: str,
        imap_port: int,
        encrypted_password: str,
        is_enabled: bool = True,
        health_status: str = "unknown",
    ) -> Mailbox:
        mailbox = Mailbox(
            user_id=user_id,
            email_address=email_address.strip().lower(),
            imap_username=imap_username.strip(),
            imap_host=imap_host.strip(),
            imap_port=imap_port,
            encrypted_password=encrypted_password,
            is_enabled=is_enabled,
            health_status=health_status,
        )
        self._session.add(mailbox)
        await self._session.commit()
        await self._session.refresh(mailbox)
        return mailbox

    async def save(self, mailbox: Mailbox) -> Mailbox:
        self._session.add(mailbox)
        await self._session.commit()
        await self._session.refresh(mailbox)
        return mailbox

    async def record_health(self, mailbox: Mailbox, health_status: str, error_message: Optional[str] = None, synced: bool = False) -> None:
        mailbox.health_status = health_status
        if error_message:
            mailbox.last_error_message = error_message
            mailbox.last_error_at = datetime.now(timezone.utc)
        if synced:
            mailbox.last_sync_at = datetime.now(timezone.utc)
        return await self.save(mailbox)

    async def soft_delete(self, mailbox: Mailbox) -> None:
        mailbox.deleted_at = datetime.now(timezone.utc)
        await self.save(mailbox)
