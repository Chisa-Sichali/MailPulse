import asyncio
from uuid import UUID

from arq import cron

from app.core.logging import get_logger, setup_logging
from app.services.email_processing.event_service import EmailProcessingService
from app.services.webhook.webhook_service import WebhookDispatcher
from app.workers.db import worker_session

logger = get_logger(__name__)


async def startup(_ctx) -> None:
    setup_logging()
    logger.info("MailPulse worker started")


async def shutdown(_ctx) -> None:
    logger.info("MailPulse worker shutting down")


async def monitor_mailboxes(_ctx) -> dict:
    async with worker_session() as session:
        service = EmailProcessingService(session)
        enqueued = await service.poll_all_enabled_mailboxes()

    if enqueued == 0:
        logger.info("Monitor sweep completed with no new email jobs enqueued")
    else:
        logger.info("Monitor sweep enqueued %s email job(s)", enqueued)
    return {"enqueued": enqueued}


async def process_email_message(_ctx, mailbox_id: str, imap_uid: str) -> dict:
    from app.core.queue import enqueue_dispatch_webhook

    job_try = _ctx.get("job_try", 1)
    event_id: UUID | None = None
    should_dispatch = False

    async with worker_session() as session:
        service = EmailProcessingService(session)
        event_id, should_dispatch = await service.process_imap_message(
            mailbox_id=UUID(mailbox_id),
            imap_uid=imap_uid,
            job_try=job_try,
        )

    if event_id is not None and should_dispatch:
        await enqueue_dispatch_webhook(email_event_id=event_id)

    return {
        "event_id": str(event_id) if event_id else None,
        "dispatched": should_dispatch,
    }


async def dispatch_webhook(_ctx, email_event_id: str) -> dict:
    async with worker_session() as session:
        dispatcher = WebhookDispatcher(session)
        enqueued = await dispatcher.fan_out_event(email_event_id=UUID(email_event_id))

    logger.info("Fan-out enqueued %s webhook delivery job(s) for event %s", enqueued, email_event_id)
    return {"enqueued": enqueued}


async def deliver_webhook(_ctx, delivery_id: str) -> dict:
    job_try = _ctx.get("job_try", 1)

    async with worker_session() as session:
        dispatcher = WebhookDispatcher(session)
        delivery = await dispatcher.deliver(
            delivery_id=UUID(delivery_id),
            job_try=job_try,
        )

    return {
        "delivery_id": delivery_id,
        "status": delivery.status,
        "attempt_count": delivery.attempt_count,
    }


async def retry_failed_webhook_deliveries(_ctx) -> dict:
    async with worker_session() as session:
        dispatcher = WebhookDispatcher(session)
        enqueued = await dispatcher.retry_due_deliveries()

    if enqueued == 0:
        logger.info("No failed webhook deliveries were ready for retry")
    else:
        logger.info("Re-queued %s failed webhook delivery job(s)", enqueued)
    return {"enqueued": enqueued}
