# MailPulse

A modern email event processing platform that converts IMAP inbox activity into real-time webhook events with retries, analytics, and monitoring.

---

## Problem

Integrating incoming email into applications is notoriously difficult. Developers often resort to writing custom scripts to maintain persistent IMAP connections or constantly poll inboxes. This approach is unreliable, resource-intensive, and prone to breaking when parsing complex MIME structures, handling attachments, or dealing with network instability. Developers need a reliable, webhook-based stream of email data, similar to how modern payment gateways handle transaction events.

---

## Solution

MailPulse bridges the gap between legacy email protocols and modern web architectures. It handles the heavy lifting of polling, parsing, and error recovery, providing you with clean, structured JSON payloads via webhooks.

**Architecture Overview:**
Email → IMAP Listener → Event Processor → Queue → Webhook Dispatcher → Client App

---

## Features

- **Multi-mailbox IMAP monitoring**: Connect and monitor multiple inboxes simultaneously.
- **Real-time email event processing**: Fast parsing and normalization of email bodies and attachments.
- **Webhook delivery system**: Secure, fan-out webhook dispatch.
- **Retry mechanism with backoff**: Built-in exponential backoff for failed deliveries.
- **Dead letter queue**: Graceful handling of permanently failed webhooks.
- **Event logs & analytics**: Track email volume and delivery success rates.
- **API key authentication**: Secure endpoints for programmatic access.

---

## Architecture

```text
+----------------+      +-------------------+      +------------------+
|                |      |                   |      |                  |
|  IMAP Servers  | ---> | MailPulse Worker  | ---> | PostgreSQL DB    |
|  (Gmail, etc.) | Poll | (Arq + Redis)     | Save | (Events & Config)|
|                |      |                   |      |                  |
+----------------+      +-------------------+      +------------------+
                                |
                                | Enqueue Delivery
                                v
                        +-------------------+      +------------------+
                        |                   |      |                  |
                        | Webhook Dispatch  | ---> | Client Webhook   |
                        | (Retries/Backoff) | POST | URL              |
                        |                   |      |                  |
                        +-------------------+      +------------------+
```

---

## Tech Stack

**Backend:**
- Python 3.11+
- FastAPI
- PostgreSQL (Asyncpg)
- Redis
- Arq (Background Jobs)
- Alembic (Migrations)

**Frontend:**
- React (Vite)
- Tailwind CSS

---

## Getting Started

### 1. Clone & Environment Setup
Clone the repository and configure your environment:
```bash
cp .env.example .env
# Edit .env with your secrets
```

### 2. Start Services via Docker Compose
The easiest way to run the entire stack (PostgreSQL, Redis, API, Worker, and Dashboard) is using Docker Compose:
```bash
docker compose up -d
```
The API will be available at `http://localhost:8080` and the Dashboard at `http://localhost:3000`.

### 3. Local Development (Optional)
If developing locally without Docker for the app tier:
```bash
# Start infrastructure
docker compose up -d postgres redis

# Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start API and Worker
uvicorn app.main:app --reload --port 8080
arq app.workers.settings.WorkerSettings
```

---

## Example Event Payload

When MailPulse receives an email, it sends a signed POST request to your webhook URL with a payload similar to this:

```json
{
  "id": "event_uuid",
  "type": "email.received",
  "created_at": "2026-06-21T12:00:00Z",
  "data": {
    "message_id": "<example@mailpulse.local>",
    "mailbox_id": "mailbox_uuid",
    "from": {"email": "user@example.com", "name": "User Name"},
    "to": ["support@company.com"],
    "subject": "Hello",
    "text_body": "This is the body of the email.",
    "html_body": "<p>This is the body of the email.</p>",
    "attachments": [],
    "in_reply_to": null,
    "received_at": "2026-06-21T11:59:50Z"
  }
}
```

---

## Why MailPulse

- **Developer Productivity:** Stop writing brittle IMAP parsers and focus on your core application logic.
- **Event-Driven Architecture:** Treat emails like any other webhook event in your system.
- **Production-Ready Design:** Built with resilience in mind, featuring retries, exponential backoff, and dead-letter queues.
- **Extensibility:** Easily add custom parsing logic or new dispatch mechanisms.

---

## Future Improvements

- Rules engine for filtering emails before dispatch.
- Webhook inspector UI for detailed delivery debugging.
- Event replay functionality.
- Multi-tenant SaaS support.
- Expanded UI dashboard capabilities.
