import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.email_event import EmailEvent, EmailEventStatus
from app.database.models.mailbox import Mailbox
from app.database.models.webhook import Webhook, WebhookDelivery, WebhookDeliveryStatus


class AnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    @staticmethod
    def _period_start(days: int) -> datetime:
        return datetime.now(timezone.utc) - timedelta(days=days)

    @staticmethod
    def _date_range(days: int) -> list[str]:
        today = datetime.now(timezone.utc).date()
        start = today - timedelta(days=days - 1)
        return [(start + timedelta(days=offset)).isoformat() for offset in range(days)]

    async def get_overview(self, *, user_id: uuid.UUID, days: int = 7) -> dict[str, Any]:
        period_start = self._period_start(days)

        emails_period_stmt = (
            select(func.count(EmailEvent.id))
            .join(Mailbox)
            .where(
                Mailbox.user_id == user_id,
                Mailbox.deleted_at.is_(None),
                EmailEvent.created_at >= period_start,
            )
        )
        failed_events_stmt = (
            select(func.count(func.distinct(EmailEvent.id)))
            .join(Mailbox, EmailEvent.mailbox_id == Mailbox.id)
            .outerjoin(WebhookDelivery, WebhookDelivery.email_event_id == EmailEvent.id)
            .where(
                Mailbox.user_id == user_id,
                Mailbox.deleted_at.is_(None),
                EmailEvent.created_at >= period_start,
                (
                    EmailEvent.status.in_(
                        [
                            EmailEventStatus.FAILED.value,
                            EmailEventStatus.DEAD_LETTERED.value,
                        ]
                    )
                    | WebhookDelivery.status.in_(
                        [
                            WebhookDeliveryStatus.FAILED.value,
                            WebhookDeliveryStatus.DEAD_LETTERED.value,
                        ]
                    )
                    | (
                        (EmailEvent.status == EmailEventStatus.PENDING.value)
                        & (EmailEvent.error_message.is_not(None))
                    )
                ),
            )
        )
        total_events_stmt = (
            select(func.count(EmailEvent.id))
            .join(Mailbox)
            .where(Mailbox.user_id == user_id, Mailbox.deleted_at.is_(None))
        )
        delivery_counts_stmt = (
            select(
                func.count(WebhookDelivery.id),
                func.count(WebhookDelivery.id).filter(
                    WebhookDelivery.status == WebhookDeliveryStatus.DELIVERED.value
                ),
                func.count(WebhookDelivery.id).filter(
                    WebhookDelivery.status.in_(
                        [
                            WebhookDeliveryStatus.FAILED.value,
                            WebhookDeliveryStatus.DEAD_LETTERED.value,
                        ]
                    )
                ),
                func.count(WebhookDelivery.id).filter(
                    WebhookDelivery.status == WebhookDeliveryStatus.PENDING.value
                ),
            )
            .join(EmailEvent, WebhookDelivery.email_event_id == EmailEvent.id)
            .join(Mailbox, EmailEvent.mailbox_id == Mailbox.id)
            .where(
                Mailbox.user_id == user_id,
                Mailbox.deleted_at.is_(None),
                WebhookDelivery.created_at >= period_start,
            )
        )
        avg_latency_stmt = (
            select(
                func.avg(
                    func.extract(
                        "epoch",
                        EmailEvent.processed_at - EmailEvent.created_at,
                    )
                    * 1000.0
                )
            )
            .join(Mailbox)
            .where(
                Mailbox.user_id == user_id,
                Mailbox.deleted_at.is_(None),
                EmailEvent.created_at >= period_start,
                EmailEvent.processed_at.is_not(None),
            )
        )

        session = self._session
        total_events = (await session.execute(total_events_stmt)).scalar_one()
        emails_period = (await session.execute(emails_period_stmt)).scalar_one()
        failed_events = (await session.execute(failed_events_stmt)).scalar_one()
        deliveries_total, deliveries_success, deliveries_failed, deliveries_pending = (
            await session.execute(delivery_counts_stmt)
        ).one()
        avg_latency = (await session.execute(avg_latency_stmt)).scalar_one()

        success_rate = (
            round((deliveries_success / deliveries_total) * 100, 2)
            if deliveries_total
            else 0.0
        )
        failure_rate = (
            round((deliveries_failed / deliveries_total) * 100, 2)
            if deliveries_total
            else 0.0
        )

        return {
            "emails_processed_total": int(total_events or 0),
            "emails_processed_period": int(emails_period or 0),
            "events_failed": int(failed_events or 0),
            "webhook_deliveries_total": int(deliveries_total or 0),
            "webhook_deliveries_success": int(deliveries_success or 0),
            "webhook_deliveries_failed": int(deliveries_failed or 0),
            "webhook_deliveries_pending": int(deliveries_pending or 0),
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "avg_processing_latency_ms": round(float(avg_latency), 2)
            if avg_latency is not None
            else None,
        }

    async def get_top_senders(
        self,
        *,
        user_id: uuid.UUID,
        days: int = 7,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        period_start = self._period_start(days)
        stmt = (
            select(
                EmailEvent.sender_email,
                func.coalesce(EmailEvent.sender_name, "").label("sender_name"),
                func.count(EmailEvent.id).label("count"),
            )
            .join(Mailbox)
            .where(
                Mailbox.user_id == user_id,
                Mailbox.deleted_at.is_(None),
                EmailEvent.created_at >= period_start,
            )
            .group_by(EmailEvent.sender_email, EmailEvent.sender_name)
            .order_by(func.count(EmailEvent.id).desc(), EmailEvent.sender_email.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [
            {
                "sender_email": row.sender_email,
                "sender_name": row.sender_name or "",
                "count": int(row.count or 0),
            }
            for row in result.all()
        ]

    async def get_volume(self, *, user_id: uuid.UUID, days: int = 30) -> list[dict[str, Any]]:
        from sqlalchemy import text
        period_start = self._period_start(days)
        stmt = (
            select(
                func.date_trunc("day", EmailEvent.created_at).label("day"),
                func.count(EmailEvent.id).label("count"),
            )
            .join(Mailbox)
            .where(
                Mailbox.user_id == user_id,
                Mailbox.deleted_at.is_(None),
                EmailEvent.created_at >= period_start,
            )
            .group_by(text("day"))
            .order_by(text("day ASC"))
        )
        result = await self._session.execute(stmt)
        rows = {row.day.date().isoformat(): int(row.count or 0) for row in result.all()}

        return [{"date": day, "count": rows.get(day, 0)} for day in self._date_range(days)]

    async def get_webhook_performance(
        self,
        *,
        user_id: uuid.UUID,
        days: int = 7,
    ) -> list[dict[str, Any]]:
        period_start = self._period_start(days)
        stmt = (
            select(
                Webhook.id.label("webhook_id"),
                Webhook.name,
                Webhook.url,
                func.count(WebhookDelivery.id).label("total_deliveries"),
                func.count(WebhookDelivery.id).filter(
                    WebhookDelivery.status == WebhookDeliveryStatus.DELIVERED.value
                ).label("delivered"),
                func.count(WebhookDelivery.id).filter(
                    WebhookDelivery.status == WebhookDeliveryStatus.FAILED.value
                ).label("failed"),
            )
            .join(
                WebhookDelivery,
                and_(
                    WebhookDelivery.webhook_id == Webhook.id,
                    WebhookDelivery.created_at >= period_start,
                ),
                isouter=True,
            )
            .where(Webhook.user_id == user_id, Webhook.deleted_at.is_(None))
            .group_by(Webhook.id, Webhook.name, Webhook.url)
            .order_by(func.count(WebhookDelivery.id).desc(), Webhook.url.asc())
        )
        result = await self._session.execute(stmt)
        rows = []
        for row in result.all():
            total = int(row.total_deliveries or 0)
            success_rate = round((int(row.delivered or 0) / total) * 100, 2) if total else 0.0
            rows.append(
                {
                    "webhook_id": str(row.webhook_id),
                    "name": row.name,
                    "url": row.url,
                    "total_deliveries": total,
                    "delivered": int(row.delivered or 0),
                    "failed": int(row.failed or 0),
                    "success_rate": success_rate,
                }
            )
        return rows

    async def count_resources(self, *, user_id: uuid.UUID) -> dict[str, int]:
        mailbox_stmt = select(
            func.count(Mailbox.id),
            func.count(Mailbox.id).filter(Mailbox.is_enabled.is_(True)),
        ).where(
            Mailbox.user_id == user_id,
            Mailbox.deleted_at.is_(None),
        )
        webhook_stmt = select(func.count(Webhook.id)).where(
            Webhook.user_id == user_id,
            Webhook.deleted_at.is_(None),
        )
        mailbox_result = await self._session.execute(mailbox_stmt)
        webhook_result = await self._session.execute(webhook_stmt)
        mailboxes, enabled_mailboxes = mailbox_result.one()
        (webhooks,) = webhook_result.one()
        return {
            "mailboxes": int(mailboxes or 0),
            "enabled_mailboxes": int(enabled_mailboxes or 0),
            "webhooks": int(webhooks or 0),
        }
