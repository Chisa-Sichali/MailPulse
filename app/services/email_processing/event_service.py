import uuid
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.core.security.encryption import decrypt_secret
from app.database.models.email_event import EmailEventStatus
from app.database.models.mailbox import MailboxHealthStatus
from app.database.repositories.email_event_repository import EmailEventRepository
from app.database.repositories.mailbox_repository import MailboxRepository
from app.services.email_processing.email_parser import parse_email_message
from app.services.email_processing.imap_client import ImapClient, ImapCredentials

logger = get_logger(__name__)


class EmailProcessingService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._mailboxes = MailboxRepository(session)
        self._events = EmailEventRepository(session)
        self._settings = get_settings()

    async def process_imap_message(
        self,
        *,
        mailbox_id: uuid.UUID,
        imap_uid: str,
        job_try: int = 1,
    ) -> tuple[uuid.UUID | None, bool]:
        mailbox = await self._mailboxes.get_by_id(mailbox_id)
        if mailbox is None or not mailbox.is_enabled:
            logger.warning("Mailbox %s not found or disabled", mailbox_id)
            return None, False

        password = decrypt_secret(mailbox.encrypted_password)
        credentials = ImapCredentials(
            host=mailbox.imap_host,
            port=mailbox.imap_port,
            username=mailbox.imap_username,
            password=password,
        )

        try:
            with ImapClient(credentials) as imap:
                raw_email = imap.fetch_rfc822(imap_uid)
                parsed = parse_email_message(raw_email)

                existing = await self._events.get_by_message_id(
                    mailbox_id=mailbox.id,
                    message_id=parsed.message_id,
                )
                if existing is not None:
                    imap.mark_as_seen(imap_uid)
                    logger.info(
                        "Duplicate message %s for mailbox %s; marked seen",
                        parsed.message_id,
                        mailbox.id,
                    )
                    return existing.id, False

                event = await self._events.create_from_parsed(
                    mailbox_id=mailbox.id,
                    message_id=parsed.message_id,
                    imap_uid=imap_uid,
                    sender_email=parsed.sender_email,
                    sender_name=parsed.sender_name,
                    recipients=parsed.recipients,
                    subject=parsed.subject,
                    text_body=parsed.text_body,
                    html_body=parsed.html_body,
                    attachments_metadata=[item.to_dict() for item in parsed.attachments],
                    in_reply_to=parsed.in_reply_to,
                    received_at=parsed.received_at,
                )
                await self._events.mark_processed(event)
                imap.mark_as_seen(imap_uid)

            await self._mailboxes.record_health(
                mailbox,
                health_status=MailboxHealthStatus.HEALTHY.value,
                synced=True,
            )
            logger.info("Processed email event %s for mailbox %s", event.id, mailbox.id)
            return event.id, True

        except Exception as exc:
            logger.exception(
                "Failed processing mailbox=%s uid=%s try=%s",
                mailbox_id,
                imap_uid,
                job_try,
            )
            await self._mailboxes.record_health(
                mailbox,
                health_status=MailboxHealthStatus.DEGRADED.value,
                error_message=str(exc),
            )
            if job_try >= self._settings.arq_max_tries:
                logger.error(
                    "Max retries reached for mailbox=%s uid=%s; moving to dead letter queue",
                    mailbox_id,
                    imap_uid,
                )
            raise

    async def poll_mailbox(self, mailbox_id: uuid.UUID) -> list[str]:
        from app.core.queue import enqueue_process_email

        mailbox = await self._mailboxes.get_by_id(mailbox_id)
        if mailbox is None or not mailbox.is_enabled:
            return []

        password = decrypt_secret(mailbox.encrypted_password)
        credentials = ImapCredentials(
            host=mailbox.imap_host,
            port=mailbox.imap_port,
            username=mailbox.imap_username,
            password=password,
        )

        uids: list[str] = []
        try:
            with ImapClient(credentials) as imap:
                uids = imap.search_unseen_uids()

            for uid in uids:
                await enqueue_process_email(mailbox_id=mailbox.id, imap_uid=uid)

            await self._mailboxes.record_health(
                mailbox,
                health_status=MailboxHealthStatus.HEALTHY.value,
                synced=True,
            )
        except Exception as exc:
            logger.warning("Mailbox poll failed for %s: %s", mailbox_id, exc)
            await self._mailboxes.record_health(
                mailbox,
                health_status=MailboxHealthStatus.ERROR.value,
                error_message=str(exc),
            )
            raise

        return uids

    async def poll_all_enabled_mailboxes(self) -> int:
        mailboxes = await self._mailboxes.list_enabled()
        enqueued = 0

        for mailbox in mailboxes:
            try:
                uids = await self.poll_mailbox(mailbox.id)
                enqueued += len(uids)
            except Exception:
                continue

        return enqueued


class EmailEventService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._events = EmailEventRepository(session)

    async def list_events(
        self,
        *,
        user_id: uuid.UUID,
        mailbox_id: uuid.UUID | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ):
        if status and status not in {item.value for item in EmailEventStatus}:
            raise ValidationError("Invalid event status filter")

        return await self._events.list_for_user(
            user_id=user_id,
            mailbox_id=mailbox_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def get_event(self, *, user_id: uuid.UUID, event_id: uuid.UUID):
        event = await self._events.get_by_id_for_user(event_id, user_id)
        if event is None:
            raise NotFoundError("Email event not found")
        return event

    async def retry_event(self, *, user_id: uuid.UUID, event_id: uuid.UUID) -> None:
        from app.core.queue import enqueue_dispatch_webhook

        event = await self.get_event(user_id=user_id, event_id=event_id)
        if event.status not in {
            EmailEventStatus.FAILED.value,
            EmailEventStatus.DEAD_LETTERED.value,
            EmailEventStatus.PENDING.value,
        }:
            raise ValidationError("Only failed or pending events can be retried")

        await self._events.mark_pending_retry(event)

        # The event is already parsed and stored in the database.
        # We only need to retry the webhook fan-out and delivery.
        await enqueue_dispatch_webhook(email_event_id=event.id)
