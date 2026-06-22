from uuid import UUID

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.config import get_settings

_pool: ArqRedis | None = None


def _redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(get_settings().redis_url)


async def get_arq_pool() -> ArqRedis:
    global _pool
    if _pool is None:
        _pool = await create_pool(_redis_settings())
    return _pool


async def close_arq_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def enqueue_monitor_sweep() -> str | None:
    pool = await get_arq_pool()
    job = await pool.enqueue_job("monitor_mailboxes")
    return job.job_id if job else None


async def enqueue_process_email(*, mailbox_id: UUID, imap_uid: str) -> str | None:
    pool = await get_arq_pool()
    job = await pool.enqueue_job(
        "process_email_message",
        str(mailbox_id),
        imap_uid,
        _job_id=f"process-email:{mailbox_id}:{imap_uid}",
    )
    return job.job_id if job else None


async def enqueue_dispatch_webhook(*, email_event_id: UUID) -> str | None:
    pool = await get_arq_pool()
    job = await pool.enqueue_job(
        "dispatch_webhook",
        str(email_event_id),
        _job_id=f"dispatch-webhook:{email_event_id}",
    )
    return job.job_id if job else None


async def enqueue_deliver_webhook(*, delivery_id: UUID) -> str | None:
    pool = await get_arq_pool()
    job = await pool.enqueue_job(
        "deliver_webhook",
        str(delivery_id),
        _job_id=f"deliver-webhook:{delivery_id}",
    )
    return job.job_id if job else None
