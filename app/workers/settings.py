from arq import cron
from arq.connections import RedisSettings

from app.core.config import get_settings
from app.workers.tasks import (
    deliver_webhook,
    dispatch_webhook,
    monitor_mailboxes,
    process_email_message,
    retry_failed_webhook_deliveries,
    shutdown,
    startup,
)


def _build_cron_jobs():
    settings = get_settings()
    interval_seconds = max(30, settings.email_monitor_poll_interval_seconds)
    interval_minutes = max(1, interval_seconds // 60)
    interval_second_step = max(1, interval_seconds)

    monitor_kwargs = (
        {"second": set(range(0, 60, interval_second_step))}
        if interval_seconds < 60
        else {"minute": set(range(0, 60, interval_minutes))}
    )
    return [
        cron(
            monitor_mailboxes,
            **monitor_kwargs,
            run_at_startup=True,
        ),
        cron(
            retry_failed_webhook_deliveries,
            minute=set(range(0, 60)),
            run_at_startup=False,
        ),
    ]


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    functions = [
        monitor_mailboxes,
        process_email_message,
        dispatch_webhook,
        deliver_webhook,
        retry_failed_webhook_deliveries,
    ]
    on_startup = startup
    on_shutdown = shutdown
    max_tries = get_settings().arq_max_tries
    job_timeout = get_settings().arq_job_timeout
    cron_jobs = _build_cron_jobs()
