import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.core.security.encryption import decrypt_secret, encrypt_secret
from app.core.security.webhook_signature import sign_webhook_payload
from app.database.models.email_event import EmailEvent
from app.database.models.user import User
from app.database.models.webhook import Webhook, WebhookDelivery, WebhookDeliveryStatus
from app.database.repositories.mailbox_repository import MailboxRepository
from app.database.repositories.webhook_delivery_repository import WebhookDeliveryRepository
from app.database.repositories.webhook_repository import WebhookRepository

logger = get_logger(__name__)

DEFAULT_EVENT_TYPE = "email.received"


def build_email_event_payload(event: EmailEvent) -> dict[str, Any]:
    return {
        "id": str(event.id),
        "type": DEFAULT_EVENT_TYPE,
        "created_at": event.created_at.isoformat(),
        "data": {
            "message_id": event.message_id,
            "mailbox_id": str(event.mailbox_id),
            "from": {"email": event.sender_email, "name": event.sender_name},
            "to": event.recipients,
            "subject": event.subject,
            "text_body": event.text_body,
            "html_body": event.html_body,
            "attachments": event.attachments_metadata,
            "in_reply_to": event.in_reply_to,
            "received_at": event.received_at.isoformat() if event.received_at else None,
        },
    }


def build_test_payload() -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": str(uuid.uuid4()),
        "type": DEFAULT_EVENT_TYPE,
        "created_at": now,
        "data": {
            "message_id": "<test@mailpulse.local>",
            "mailbox_id": str(uuid.uuid4()),
            "from": {"email": "test@example.com", "name": "MailPulse Test"},
            "to": ["you@example.com"],
            "subject": "MailPulse webhook test",
            "text_body": "This is a test webhook delivery from MailPulse.",
            "html_body": "",
            "attachments": [],
            "in_reply_to": None,
            "received_at": now,
        },
    }


class WebhookDispatcher:
    def __init__(self, session) -> None:
        self._session = session
        self._webhooks = WebhookRepository(session)
        self._deliveries = WebhookDeliveryRepository(session)
        self._mailboxes = MailboxRepository(session)
        self._settings = get_settings()

    def _retry_delay_seconds(self, attempt_count: int) -> int | None:
        delays = self._settings.webhook_retry_delays_seconds
        index = attempt_count - 1
        if index < 0 or index >= len(delays):
            return None
        return delays[index]

    async def fan_out_event(self, *, email_event_id: uuid.UUID) -> int:
        from app.database.repositories.email_event_repository import EmailEventRepository

        events = EmailEventRepository(self._session)
        event = await events.get_by_id(email_event_id)
        if event is None:
            logger.warning("Email event %s not found for webhook fan-out", email_event_id)
            return 0

        mailbox = await self._mailboxes.get_by_id(event.mailbox_id)
        if mailbox is None:
            return 0

        webhooks = await self._webhooks.list_enabled_for_user(
            mailbox.user_id,
            event_type=DEFAULT_EVENT_TYPE,
        )

        if not webhooks:
            logger.info("No enabled webhooks for user %s", mailbox.user_id)
            return 0

        from app.core.queue import enqueue_deliver_webhook

        enqueued = 0
        for webhook in webhooks:
            delivery = await self._deliveries.get_or_create_pending(
                webhook_id=webhook.id,
                email_event_id=event.id,
            )
            if delivery.status == WebhookDeliveryStatus.DELIVERED.value:
                continue
            await enqueue_deliver_webhook(delivery_id=delivery.id)
            enqueued += 1

        return enqueued

    async def deliver(
        self,
        *,
        delivery_id: uuid.UUID,
        job_try: int = 1,
    ) -> WebhookDelivery:
        from app.database.repositories.email_event_repository import EmailEventRepository

        delivery = await self._deliveries.get_by_id(delivery_id)
        if delivery is None:
            raise NotFoundError("Webhook delivery not found")

        if delivery.status == WebhookDeliveryStatus.DELIVERED.value:
            return delivery

        webhook = await self._webhooks.get_by_id(delivery.webhook_id)
        if webhook is None or not webhook.is_enabled:
            raise NotFoundError("Webhook not found or disabled")

        events = EmailEventRepository(self._session)
        event = await events.get_by_id(delivery.email_event_id)
        if event is None:
            raise NotFoundError("Email event not found")

        payload = build_email_event_payload(event)
        secret = decrypt_secret(webhook.encrypted_secret)
        signature_header, body = sign_webhook_payload(secret=secret, payload=payload)

        headers = {
            "Content-Type": "application/json",
            "MailPulse-Signature": signature_header,
            "MailPulse-Event-Id": str(event.id),
            "MailPulse-Webhook-Id": str(webhook.id),
            "User-Agent": "MailPulse-Webhook/1.0",
        }

        try:
            response = await asyncio.to_thread(
                self._post_webhook,
                webhook.url,
                body,
                headers,
            )
            response_body = response.text[:2000] if response.text else None
            if response.is_success:
                return await self._deliveries.mark_delivered(
                    delivery,
                    http_status_code=response.status_code,
                    response_body=response_body,
                )

            attempt_count = delivery.attempt_count + 1
            dead_letter = attempt_count >= self._settings.webhook_max_attempts
            delay = self._retry_delay_seconds(attempt_count)
            next_retry = (
                datetime.now(timezone.utc) + timedelta(seconds=delay)
                if delay and not dead_letter
                else None
            )
            return await self._deliveries.mark_failed(
                delivery,
                http_status_code=response.status_code,
                response_body=response_body,
                error_message=f"HTTP {response.status_code}",
                next_retry_at=next_retry,
                dead_letter=dead_letter,
            )

        except Exception as exc:
            attempt_count = delivery.attempt_count + 1
            dead_letter = attempt_count >= self._settings.webhook_max_attempts or job_try >= self._settings.arq_max_tries
            delay = self._retry_delay_seconds(attempt_count)
            next_retry = (
                datetime.now(timezone.utc) + timedelta(seconds=delay)
                if delay and not dead_letter
                else None
            )
            logger.warning("Webhook delivery %s failed: %s", delivery_id, exc)
            return await self._deliveries.mark_failed(
                delivery,
                http_status_code=None,
                response_body=None,
                error_message=str(exc),
                next_retry_at=next_retry,
                dead_letter=dead_letter,
            )

    async def deliver_test(self, *, webhook: Webhook) -> tuple[int, str]:
        payload = build_test_payload()
        secret = decrypt_secret(webhook.encrypted_secret)
        signature_header, body = sign_webhook_payload(secret=secret, payload=payload)
        headers = {
            "Content-Type": "application/json",
            "MailPulse-Signature": signature_header,
            "MailPulse-Event-Id": payload["id"],
            "MailPulse-Webhook-Id": str(webhook.id),
            "User-Agent": "MailPulse-Webhook/1.0",
        }
        response = await asyncio.to_thread(
            self._post_webhook,
            webhook.url,
            body,
            headers,
        )
        return response.status_code, response.text[:2000] if response.text else ""

    async def retry_due_deliveries(self) -> int:
        from app.core.queue import enqueue_deliver_webhook

        due = await self._deliveries.list_due_for_retry()
        for delivery in due:
            await enqueue_deliver_webhook(delivery_id=delivery.id)
        return len(due)

    @staticmethod
    def _post_webhook(url: str, body: str, headers: dict[str, str]) -> httpx.Response:
        with httpx.Client(timeout=30.0) as client:
            return client.post(url, content=body, headers=headers)


class WebhookService:
    def __init__(self, session) -> None:
        self._session = session
        self._webhooks = WebhookRepository(session)
        self._dispatcher = WebhookDispatcher(session)

    async def create_webhook(
        self,
        *,
        user: User,
        url: str,
        name: str | None = None,
        event_types: list[str] | None = None,
        is_enabled: bool = True,
    ) -> tuple[Webhook, str]:
        if event_types is not None and DEFAULT_EVENT_TYPE not in event_types:
            raise ValidationError(f"Event types must include '{DEFAULT_EVENT_TYPE}'")

        secret = WebhookRepository.generate_secret()
        webhook = await self._webhooks.create(
            user_id=user.id,
            url=url,
            name=name,
            encrypted_secret=encrypt_secret(secret),
            secret_prefix=secret[:12],
            event_types=event_types,
            is_enabled=is_enabled,
        )
        return webhook, secret

    async def list_webhooks(self, *, user: User) -> list[Webhook]:
        return await self._webhooks.list_for_user(user.id)

    async def get_webhook(self, *, user: User, webhook_id: uuid.UUID) -> Webhook:
        webhook = await self._webhooks.get_by_id_for_user(webhook_id, user.id)
        if webhook is None:
            raise NotFoundError("Webhook not found")
        return webhook

    async def update_webhook(
        self,
        *,
        user: User,
        webhook_id: uuid.UUID,
        url: str | None = None,
        name: str | None = None,
        event_types: list[str] | None = None,
        is_enabled: bool | None = None,
    ) -> Webhook:
        webhook = await self.get_webhook(user=user, webhook_id=webhook_id)

        if url is not None:
            webhook.url = url.strip()
        if name is not None:
            webhook.name = name
        if event_types is not None:
            if DEFAULT_EVENT_TYPE not in event_types:
                raise ValidationError(f"Event types must include '{DEFAULT_EVENT_TYPE}'")
            webhook.event_types = event_types
        if is_enabled is not None:
            webhook.is_enabled = is_enabled

        return await self._webhooks.save(webhook)

    async def delete_webhook(self, *, user: User, webhook_id: uuid.UUID) -> None:
        webhook = await self.get_webhook(user=user, webhook_id=webhook_id)
        await self._webhooks.soft_delete(webhook)

    async def rotate_secret(self, *, user: User, webhook_id: uuid.UUID) -> tuple[Webhook, str]:
        webhook = await self.get_webhook(user=user, webhook_id=webhook_id)
        secret = WebhookRepository.generate_secret()
        webhook.encrypted_secret = encrypt_secret(secret)
        webhook.secret_prefix = secret[:12]
        await self._webhooks.save(webhook)
        return webhook, secret

    async def test_webhook(self, *, user: User, webhook_id: uuid.UUID) -> tuple[int, str]:
        webhook = await self.get_webhook(user=user, webhook_id=webhook_id)
        return await self._dispatcher.deliver_test(webhook=webhook)

    async def list_deliveries(
        self,
        *,
        user: User,
        webhook_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[WebhookDelivery]:
        await self.get_webhook(user=user, webhook_id=webhook_id)
        deliveries = WebhookDeliveryRepository(self._session)
        return await deliveries.list_for_webhook_for_user(
            webhook_id=webhook_id,
            user_id=user.id,
            limit=limit,
            offset=offset,
        )
