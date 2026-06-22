# Queues and Workers

MailPulse relies on background workers to process emails and dispatch webhooks asynchronously. It uses [Arq](https://arq-docs.helpmanual.io/), a fast job queuing and RPC library for Python, backed by Redis.

## Job Types

1. **`monitor_mailboxes`**: A scheduled (cron) task that polls all active IMAP mailboxes for new unseen emails. It enqueues `process_email_message` tasks.
2. **`process_email_message`**: Fetches the raw email from IMAP, parses it, creates an `EmailEvent` in the database, marks the message as seen, and enqueues `dispatch_webhook`.
3. **`dispatch_webhook`**: Finds all active webhooks for the user associated with the received email and enqueues a `deliver_webhook` job for each.
4. **`deliver_webhook`**: Handles the HTTP POST request to the destination URL. It signs the payload and records the success or failure. If it fails, it schedules a retry based on the backoff strategy.
5. **`retry_failed_webhook_deliveries`**: A scheduled (cron) task that scans the database for deliveries whose `next_retry_at` time has passed, re-enqueuing them for delivery.

## Configuration
Worker settings are defined in `app/workers/settings.py` and are configured via environment variables:
- `EMAIL_MONITOR_POLL_INTERVAL_SECONDS`: How often the IMAP polling occurs.
- `ARQ_MAX_TRIES`: The maximum number of retries for an Arq job.
- `ARQ_JOB_TIMEOUT`: The maximum time a job can run before timing out.
- `WEBHOOK_MAX_ATTEMPTS`: The maximum number of delivery attempts for a webhook.
