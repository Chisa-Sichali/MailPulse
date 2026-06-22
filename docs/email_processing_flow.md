# Email Processing Flow

This document details how an email travels from an IMAP server to a saved event in MailPulse.

## 1. IMAP Polling Mechanism
A cron job, configured in the Arq worker (`app/workers/settings.py`), triggers the `monitor_mailboxes` task at regular intervals (defined by `EMAIL_MONITOR_POLL_INTERVAL_SECONDS`).
This sweep iterates over all active mailboxes and runs an IMAP `SEARCH UNSEEN` command.

## 2. Job Enqueueing
For every unseen UID found, an individual `process_email_message` job is enqueued in Redis. This allows processing multiple emails concurrently.

## 3. Email Parsing Logic
The worker fetches the raw `RFC822` email payload. The parsing module (`app/services/email_processing/email_parser.py`):
- Extracts headers (From, To, Subject, Message-ID, In-Reply-To).
- Cleans and decodes the text and HTML body.
- Extracts attachment metadata (filenames, content types, sizes).

## 4. Event Creation & Marking Seen
The parsed data is saved to PostgreSQL as an `EmailEvent`. To prevent duplicate processing, the system checks if the `Message-ID` already exists for that mailbox. Once saved, the IMAP client marks the message with the `\Seen` flag.

## 5. Webhook Dispatch Trigger
Immediately after saving the event, the worker enqueues a `dispatch_webhook` job to begin the fan-out process to configured webhooks.
