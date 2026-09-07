import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.webhook import Webhook, WebhookDelivery, WebhookDeliveryStatus

class WebhookDeliveryRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, delivery: WebhookDelivery) -> WebhookDelivery:
        self._session.add(delivery)
        await self._session.commit()
        await self._session.refresh(delivery)
        return delivery

    async def update(self, delivery: WebhookDelivery) -> WebhookDelivery:
        self._session.add(delivery)
        await self._session.commit()
        await self._session.refresh(delivery)
        return delivery

    async def get_by_id(self, delivery_id: uuid.UUID) -> Optional[WebhookDelivery]:
        stmt = select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_for_event_and_webhook(self, event_id: uuid.UUID, webhook_id: uuid.UUID) -> Optional[WebhookDelivery]:
        stmt = select(WebhookDelivery).where(WebhookDelivery.email_event_id == event_id, WebhookDelivery.webhook_id == webhook_id).order_by(WebhookDelivery.created_at.desc()).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_pending(
        self,
        *,
        webhook_id: uuid.UUID,
        email_event_id: uuid.UUID,
    ) -> WebhookDelivery:
        existing = await self.get_latest_for_event_and_webhook(email_event_id, webhook_id)
        if existing is not None:
            return existing

        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            email_event_id=email_event_id,
            status=WebhookDeliveryStatus.PENDING.value,
            attempt_count=0,
        )
        return await self.create(delivery)

    async def list_pending_retries(self, current_time: datetime) -> Sequence[WebhookDelivery]:
        stmt = select(WebhookDelivery).where(
            WebhookDelivery.status == WebhookDeliveryStatus.FAILED.value,
            WebhookDelivery.next_retry_at.is_not(None),
            WebhookDelivery.next_retry_at <= current_time,
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_due_for_retry(self, current_time: datetime | None = None) -> Sequence[WebhookDelivery]:
        now = current_time or datetime.now(timezone.utc)
        stmt = select(WebhookDelivery).where(
            WebhookDelivery.status == WebhookDeliveryStatus.FAILED.value,
            WebhookDelivery.next_retry_at.is_not(None),
            WebhookDelivery.next_retry_at <= now,
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_for_webhook_for_user(
        self,
        *,
        webhook_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[WebhookDelivery]:
        stmt = (
            select(WebhookDelivery)
            .join(Webhook)
            .where(
                WebhookDelivery.webhook_id == webhook_id,
                Webhook.user_id == user_id,
                Webhook.deleted_at.is_(None),
            )
            .order_by(WebhookDelivery.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def mark_delivered(
        self,
        delivery: WebhookDelivery,
        *,
        http_status_code: int | None = None,
        response_body: str | None = None,
    ) -> WebhookDelivery:
        delivery.status = WebhookDeliveryStatus.DELIVERED.value
        delivery.attempt_count += 1
        delivery.http_status_code = http_status_code
        delivery.response_body = response_body
        delivery.delivered_at = datetime.now(timezone.utc)
        delivery.next_retry_at = None
        delivery.last_error = None
        return await self.update(delivery)

    async def mark_failed(
        self,
        delivery: WebhookDelivery,
        *,
        http_status_code: int | None = None,
        response_body: str | None = None,
        error_message: str | None = None,
        next_retry_at: datetime | None = None,
        dead_letter: bool = False,
    ) -> WebhookDelivery:
        delivery.attempt_count += 1
        delivery.http_status_code = http_status_code
        delivery.response_body = response_body
        delivery.last_error = error_message
        delivery.next_retry_at = None if dead_letter else next_retry_at
        delivery.status = WebhookDeliveryStatus.DEAD_LETTERED.value if dead_letter else WebhookDeliveryStatus.FAILED.value
        return await self.update(delivery)
