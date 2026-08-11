# MailPulse

**Turn any inbox into a webhook stream.** MailPulse is an email event processing platform that monitors IMAP mailboxes, parses incoming mail into clean structured JSON, and delivers it to your webhook URLs — with retries, backoff, signing, analytics, and a management UI.

Think *Stripe for payment events, Twilio for SMS* — but for email. Stop writing brittle IMAP pollers and MIME parsers; treat incoming email like any other webhook event in your system.

> **Stack at a glance:** Python 3.11 · FastAPI · Arq · Redis · PostgreSQL · Next.js 16 · Docker

---

## How It Works

```
Email arrives → IMAP polled → parsed → saved as event → webhook fan-out → your app
```

1. You register an account and **add a mailbox** (IMAP credentials, encrypted at rest).
2. You **create a webhook** — the URL where you want email events delivered.
3. An Arq background worker **polls your mailbox** on a schedule (default: every 60s).
4. New email is **fetched and parsed** (MIME, bodies, attachments, reply threading, signatures).
5. The parsed email is **saved as an `EmailEvent`** in PostgreSQL.
6. The event is **fanned out to all your webhooks** — each delivery is HMAC-signed.
7. If your endpoint is down, MailPulse **retries with exponential backoff**, then dead-letters after 4 attempts. You can re-queue manually via the API.

## Features

| Feature | Description |
|---|---|
| 📥 Multi-mailbox IMAP monitoring | Connect and monitor multiple inboxes simultaneously |
| ⚡ Real-time email processing | Fast MIME parsing and normalization (bodies, attachments, replies, signatures) |
| 🔗 Webhook delivery system | Secure fan-out dispatch to multiple URLs per user |
| 🔁 Retry with exponential backoff | 60s → 5m → 30m → 2h, then dead-lettered |
| 🧾 Delivery history | Every attempt logged with HTTP status, response body, and next-retry time |
| 🔐 Signed payloads | HMAC-SHA256 signature header (`MailPulse-Signature`) so you can verify authenticity |
| 📊 Event logs & analytics | Email volume, top senders, delivery success rates |
| 🔑 JWT auth with refresh rotation | Short-lived access tokens + revocable, rotating refresh tokens |
| 🖥️ Dashboard | Web UI for monitoring and management (Next.js frontend, in development) |

## Architecture

```text
┌──────────────┐   poll   ┌───────────────────────┐
│  IMAP Server │◄────────┤   Arq Worker (Redis)   │
│  (Gmail…)    │          │  monitor · process     │
└──────────────┘          │  dispatch · deliver    │
                          └───────┬───────────┬────┘
                                  │ save      │ POST signed payload
                                  ▼           ▼
                          ┌──────────────┐  ┌──────────────────┐
                          │  PostgreSQL  │  │  Your App        │
                          │ events,      │  │  (webhook URL)   │
                          │ webhooks,    │  └──────────────────┘
                          │ deliveries   │
                          └──────▲───────┘
                                 │ reads/writes
                          ┌──────┴────────┐   ┌──────────────────┐
                          │  FastAPI API  │◄──│  Frontend (UI)   │
                          │   (port 8080) │   └──────────────────┘
                          └───────────────┘
```

### Design

- **Layered backend** — HTTP handlers (`app/api/`) → business logic (`app/services/`) → data access (`app/database/repositories/`) → ORM models. Pydantic schemas validate every request/response; the service layer knows nothing about HTTP.
- **Event-driven ingestion** — IMAP polling and webhook delivery are decoupled through the Redis-backed Arq queue, so a slow or failing webhook never blocks email ingestion.
- **Async everywhere** — FastAPI, async SQLAlchemy, and Arq are all async-native; blocking IMAP calls are offloaded to threads.

### Components

| Component | Tech | Role |
|---|---|---|
| API | FastAPI | REST API: auth, mailboxes, webhooks, events, analytics. Auto-generated OpenAPI docs at `/docs`. |
| Worker | Arq + Redis | Background jobs: polling, parsing, fan-out, delivery, retries. 5 jobs total. |
| Database | PostgreSQL 16 | Users, mailboxes, email events, webhooks, delivery logs. Migrated with Alembic. |
| Frontend | Next.js 16 (`frontend/`) | New management UI (App Router) — under active development. |
| Legacy dashboard | React + Vite (`dashboard/`) | Previous management UI, still shipped via Docker Compose. |

## Repository Structure

```text
MailPulse/
├── app/                 # FastAPI backend
│   ├── api/v1/          # Route handlers (auth, mailboxes, webhooks, events, analytics)
│   ├── core/            # Config, security (JWT, encryption, signing), logging, queue
│   ├── database/        # SQLAlchemy models + repositories
│   ├── schemas/         # Pydantic request/response models
│   ├── services/        # Business logic (auth, mailbox, webhook, email processing, analytics)
│   └── workers/         # Arq background job definitions
├── alembic/             # Database migrations
├── frontend/            # Next.js 16 frontend (App Router)
├── dashboard/           # Legacy React + Vite dashboard (Docker-served)
├── docs/                # Documentation (architecture, API reference, setup, deployment)
├── tests/               # pytest suite (auth, mailboxes, webhooks, events, parsing, analytics)
├── docker-compose.yml   # postgres + redis + api + worker + dashboard
├── Dockerfile           # API/worker image
└── .env.example         # Environment variable template
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+ (frontend only)
- Docker + Docker Compose (easiest path)

### Option A — Quick start with Docker

```bash
git clone https://github.com/Chisa-Sichali/MailPulse.git
cd MailPulse
cp .env.example .env        # then set your secrets (see Configuration)
docker compose up -d        # builds and starts postgres, redis, api, worker, dashboard
```

| Service | URL |
|---|---|
| API | http://localhost:8080 |
| Interactive API docs (Swagger UI) | http://localhost:8080/docs |
| Dashboard | http://localhost:3000 |

Migrations run automatically when the `api` and `worker` containers start.

### Option B — Local development (backend)

```bash
# 1. Infrastructure only (PostgreSQL on 5433, Redis)
docker compose up -d postgres redis

# 2. Python environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure + migrate
cp .env.example .env
alembic upgrade head

# 4. Run API (terminal 1) and worker (terminal 2)
uvicorn app.main:app --reload --port 8080
arq app.workers.settings.WorkerSettings
```

### Option C — Local development (frontend)

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

The frontend reads `NEXT_PUBLIC_FASTAPI_BACKEND_URL` from `frontend/.env` to reach the API.

---

## Usage

The API is fully self-documented — once running, browse **http://localhost:8080/docs** (Swagger UI) or `/redoc`. Here's the 4-step quick start:

### 1. Create an account

```bash
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"supersecret123","full_name":"You"}'
```

You immediately receive an `access_token` (JWT, valid 30 min) and a `refresh_token` (valid 7 days, single-use).

### 2. Add a mailbox

```bash
TOKEN="<your access_token>"

curl -X POST http://localhost:8080/api/v1/mailboxes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email_address":"me@gmail.com","password":"<app-password>","imap_host":"imap.gmail.com","imap_port":993}'
```

Credentials are encrypted before being stored. Use the `POST /mailboxes/{id}/test-connection` endpoint to verify IMAP connectivity.

### 3. Create a webhook

```bash
curl -X POST http://localhost:8080/api/v1/webhooks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://myapp.com/hooks/email","name":"My App","event_types":["email.received"]}'
```

**Save the returned `secret` (`whsec_…`) — it is shown only once.** You'll need it to verify incoming payloads. If you lose it, call `POST /webhooks/{id}/rotate-secret`.

### 4. Receive and verify events

Every webhook POST includes a signature header:

```
MailPulse-Signature: t=<unix-timestamp>,v1=<hmac-sha256-hex>
```

The signature is HMAC-SHA256 of `<timestamp>.<raw-request-body>` using your webhook secret. Verify it like this (Python):

```python
import hashlib, hmac, time

def verify_webhook(secret: str, body: bytes, signature_header: str, tolerance: int = 300) -> bool:
    parts = dict(item.split("=", 1) for item in signature_header.split(","))
    if abs(int(time.time()) - int(parts["t"])) > tolerance:
        return False  # replay protection
    signed_content = f'{parts["t"]}.{body.decode()}'.encode()
    expected = hmac.new(secret.encode(), signed_content, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, parts["v1"])
```

> Pass the **raw request body** (compact JSON) to the verifier — re-serializing the JSON will change the signature.

**Example payload** (`POST` to your webhook):

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

## API Overview

All endpoints are prefixed with `/api/v1/`. Protected endpoints require `Authorization: Bearer <access_token>`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` · `/auth/login` | Create account / sign in → token pair |
| `POST` | `/auth/refresh` | Rotate refresh token → new token pair |
| `POST` | `/auth/logout` | Revoke a refresh token |
| `GET` | `/auth/me` | Current user profile |
| `POST/GET/PATCH/DELETE` | `/mailboxes` · `/mailboxes/{id}` | Manage IMAP mailboxes |
| `POST` | `/mailboxes/{id}/test-connection` | Test IMAP connectivity |
| `POST/GET/PATCH/DELETE` | `/webhooks` · `/webhooks/{id}` | Manage webhooks |
| `POST` | `/webhooks/{id}/rotate-secret` · `/test` | New signing secret / send test delivery |
| `GET` | `/webhooks/{id}/deliveries` | Delivery history with retry state |
| `GET` | `/events` · `/events/{id}` | List / inspect email events |
| `POST` | `/events/{id}/retry` | Re-queue a failed or dead-lettered event |
| `GET` | `/analytics/overview` · `/top-senders` · `/volume` · `/webhooks` · `/resources` | Dashboard stats |
| `GET` | `/health/system` | Deep health check (DB + Redis + queue) |

Errors follow a consistent shape: `{"error": {"code": "...", "message": "..."}}`.

## Authentication & Security

- **Access tokens** — HS256-signed JWTs with a 30-minute expiry and a `type: "access"` claim.
- **Refresh tokens** — cryptographically random opaque strings (7 days), stored **SHA-256 hashed** in the DB and **rotated on every refresh** (the old token is revoked, so replay is detected). Logout revokes server-side.
- **Passwords** — hashed with bcrypt; never stored in plain text.
- **Mailbox credentials** — encrypted at rest with Fernet symmetric encryption (`CREDENTIAL_ENCRYPTION_KEY`).
- **Webhook payloads** — HMAC-SHA256 signed with a per-webhook secret and a timestamped, tolerance-checked header.

*Not yet implemented:* email verification, rate limiting, OAuth/social login. See `docs/authentication.md` for the full auth flow.

## Background Processing & Retries

Five Arq jobs run in the worker process:

| Job | Trigger | Purpose |
|---|---|---|
| `monitor_mailboxes` | Cron (every 60s) | Poll all enabled mailboxes for UNSEEN mail |
| `process_email_message` | Per unseen email | Fetch RFC822, parse, save event, mark seen |
| `dispatch_webhook` | New event | Fan out to all matching webhooks, create delivery records |
| `deliver_webhook` | Per delivery | Sign and POST payload, record result |
| `retry_failed_webhook_deliveries` | Cron (every 60s) | Re-queue deliveries whose retry time has passed |

**Retry schedule** (configurable via `WEBHOOK_RETRY_DELAYS_SECONDS`):

| Attempt | Delay | Total wait |
|---|---|---|
| 1st | 60s | 1 min |
| 2nd | 300s | 6 min |
| 3rd | 1800s | 36 min |
| 4th | 7200s | ~2.5 h |

After the 4th failed attempt a delivery is **dead-lettered** — it won't be retried automatically, but can be re-queued via `POST /events/{id}/retry`. Deduplication job IDs (`process-email:{mailbox}:{uid}`, …) prevent double-processing.

## Configuration

Configuration is read from environment variables (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://…@localhost:5433/mailpulse` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis / queue connection |
| `JWT_SECRET_KEY` | `change-me-in-production` | JWT signing secret — **set a strong value** |
| `CREDENTIAL_ENCRYPTION_KEY` | *(empty)* | Fernet key for mailbox password encryption |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `EMAIL_MONITOR_POLL_INTERVAL_SECONDS` | `60` | IMAP polling frequency |
| `ARQ_MAX_TRIES` | `4` | Max job retries |
| `WEBHOOK_MAX_ATTEMPTS` | `4` | Max delivery attempts |
| `CORS_ORIGINS` | `["http://localhost:5173", …]` | Allowed browser origins |

## Testing

```bash
pytest                      # async test suite, run from the repo root
```

The suite covers auth, mailboxes, webhooks (including HMAC signing and tamper detection), events, parsing, and analytics. Tests use a separate database (`TEST_DATABASE_URL`, defaults to `…@localhost:5433/mailpulse_test`).

## Deployment

- **Docker Compose** — `docker compose up -d` starts the full stack; migrations run automatically. For production, put the API and dashboard behind a reverse proxy (Nginx/Traefik/Caddy) for SSL termination and set strong `JWT_SECRET_KEY` / `CREDENTIAL_ENCRYPTION_KEY` values.
- **AWS App Runner** — an `apprunner.yaml` config is included for deploying the API as a managed service.
- **Health checks** — `GET /health/system` performs a real connectivity check against PostgreSQL and Redis and reports queue state.

## Documentation

The `docs/` folder contains deeper write-ups: [overview](docs/overview.md) · [architecture](docs/architecture.md) · [API reference](docs/api_reference.md) · [authentication](docs/authentication.md) · [database schema](docs/database_schema.md) · [email processing flow](docs/email_processing_flow.md) · [queues & workers](docs/queues_and_workers.md) · [webhook system](docs/webhook_system.md) · [development setup](docs/development_setup.md) · [deployment](docs/deployment.md)

## Roadmap

- Rules engine for filtering emails before dispatch
- Webhook inspector UI for delivery debugging
- Event replay
- Multi-tenant SaaS support
- Expanded dashboard capabilities

## License

[MIT](LICENSE)
