import uuid
import secrets
import string
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.webhook import Webhook

class WebhookRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    @staticmethod
    def generate_secret() -> str:
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for i in range(32))

    async def get_by_id(self, webhook_id: uuid.UUID) -> Optional[Webhook]:
        stmt = select(Webhook).where(Webhook.id == webhook_id, Webhook.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_for_user(self, webhook_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Webhook]:
        stmt = select(Webhook).where(Webhook.id == webhook_id, Webhook.user_id == user_id, Webhook.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID, *, limit: int = 50, offset: int = 0) -> Sequence[Webhook]:
        stmt = select(Webhook).where(Webhook.user_id == user_id, Webhook.deleted_at.is_(None)).order_by(Webhook.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_enabled_for_user(
        self,
        user_id: uuid.UUID,
        event_type: str | None = None,
    ) -> Sequence[Webhook]:
        stmt = select(Webhook).where(
            Webhook.user_id == user_id,
            Webhook.is_enabled.is_(True),
            Webhook.deleted_at.is_(None),
        )
        if event_type is not None:
            stmt = stmt.where(Webhook.event_types.contains([event_type]))
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        url: str,
        name: str | None,
        encrypted_secret: str,
        secret_prefix: str,
        event_types: list[str] | None = None,
        is_enabled: bool = True,
    ) -> Webhook:
        webhook = Webhook(
            user_id=user_id,
            url=url.strip(),
            name=name.strip() if isinstance(name, str) else name,
            encrypted_secret=encrypted_secret,
            secret_prefix=secret_prefix,
            event_types=event_types or ["email.received"],
            is_enabled=is_enabled,
        )
        self._session.add(webhook)
        await self._session.commit()
        await self._session.refresh(webhook)
        return webhook

    async def save(self, webhook: Webhook) -> Webhook:
        self._session.add(webhook)
        await self._session.commit()
        await self._session.refresh(webhook)
        return webhook

    async def soft_delete(self, webhook: Webhook) -> None:
        webhook.deleted_at = datetime.now(timezone.utc)
        await self.save(webhook)
