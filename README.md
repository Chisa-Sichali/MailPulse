# MailPulse

> **Turn any inbox into a webhook stream.**
> MailPulse monitors IMAP mailboxes, parses incoming mail into clean structured
> JSON, and delivers it to your webhook URLs — with retries, backoff, signing,
> analytics, and a management dashboard.

[![Backend CI](https://github.com/Chisa-Sichali/MailPulse/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/Chisa-Sichali/MailPulse/actions/workflows/backend-ci.yml)
[![Frontend CI](https://github.com/Chisa-Sichali/MailPulse/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/Chisa-Sichali/MailPulse/actions/workflows/frontend-ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Redis 7](https://img.shields.io/badge/Redis-7-DC382D.svg)](https://redis.io/)
---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Environment Variables](#environment-variables)
- [API](#api)
- [Authentication](#authentication)
- [Background Workers & Retries](#background-workers--retries)
- [Testing](#testing)
- [Linting & Formatting](#linting--formatting)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

MailPulse is an email event-processing platform. You register an IMAP mailbox, register one or more webhook endpoints,
and MailPulse continuously polls the mailbox, parses each new email into a structured JSON record, and POSTs it to your
webhooks with an HMAC signature.

It is intended for developers who need to **react to inbound email** in their own applications — support inboxes,
contact forms, transactional notifications, parsers, lead capture, ticket creation — without writing and maintaining a
custom IMAP poller, MIME parser, and retry layer.

The core problem MailPulse solves is the gap between IMAP (a 30-year-old stateful protocol with no delivery semantics)
and modern webhook consumers (which expect signed, retried, observable events). MailPulse makes inbound email behave
like any other webhook source in your system.

---

## Features

**Email ingestion**

- Multi-mailbox IMAP monitoring per user
- Configurable polling cadence (default 60 seconds, minimum 30 seconds)
- RFC822 parsing with sender, recipients, subject, text/HTML bodies, reply threading (`In-Reply-To`), and attachment
  metadata
- Deduplicated processing via per-mailbox IMAP UID job IDs

**Webhook delivery**

- HMAC-SHA256 signed payloads (header `MailPulse-Signature: t=<unix>,v1=<hex>`)
- Configurable event subscription (`email.received` today; extensible list)
- Exponential backoff retries (`60s → 5m → 30m → 2h` by default)
- Dead-letter queue after `WEBHOOK_MAX_ATTEMPTS` with manual re-queue via API
- Per-delivery audit log: HTTP status, response body, last error, next-retry time
- Manual webhook test endpoint (`POST /webhooks/{id}/test`)

**API & Auth**

- FastAPI REST API, auto-generated OpenAPI at `/docs` and `/redoc`
- JWT access tokens (HS256, 30 min) + opaque rotating refresh tokens (7 days)
- bcrypt-hashed passwords
- Fernet-encrypted mailbox credentials and webhook secrets at rest
- Per-user resource isolation

**Background processing**

- Arq (Redis-backed) worker with cron-driven mailbox polling
- Per-email and per-delivery jobs with deduplication
- Job-level retries (`ARQ_MAX_TRIES`) and timeouts (`ARQ_JOB_TIMEOUT`)

**Observability**

- Structured logging via `rich`
- Request logging middleware
- Deep health endpoint (`/health/system`) checks PostgreSQL + Redis + queue
- Analytics endpoints: overview KPIs, top senders, daily volume, per-webhook performance, resource counts

**Dashboard**

- Next.js 16 App Router UI with React Server Components
- TanStack Query for client-side caching and auto-revalidation
- shadcn/ui + Tailwind v4 component library
- Auto-refreshing access tokens via single-flight refresh

---

## Architecture

MailPulse is composed of five cooperating components:

| Component             | Responsibility                                                                                         |
|-----------------------|--------------------------------------------------------------------------------------------------------|
| **FastAPI**           | Synchronous HTTP layer: auth, mailbox/webhook/event/analytics CRUD.                                    |
| **Arq worker**        | Asynchronous layer: IMAP polling, email parsing, webhook fan-out and delivery.                         |
| **PostgreSQL**        | System of record: users, mailboxes, events, webhooks, delivery attempts.                               |
| **Redis**             | Arq job broker + cron scheduler; deduplication via job IDs.                                            |
| **Next.js dashboard** | Management UI: register mailboxes, create webhooks, view events, inspect deliveries, analytics charts. |

The API and worker share the same SQLAlchemy models and Alembic migrations but run as independent processes. The API
never blocks on IMAP or HTTP delivery — those happen in the worker. The worker never serves HTTP — it only consumes
queued jobs.

```mermaid
flowchart TB
    User([User])
    Browser([Browser])

    subgraph MailPulse
        direction TB
        Dashboard["Next.js dashboard<br/>(frontend/)"]
        API["FastAPI API<br/>(app/api/v1/*)"]
        Worker["Arq worker<br/>(app/workers/*)"]
    end

    IMAP([IMAP server<br/>Gmail, Outlook, …])
YourApp([Your webhook endpoint])

PostgreSQL[(PostgreSQL 16<br/>users, mailboxes,<br/>events, webhooks,<br/>deliveries)]
Redis[(Redis 7<br/>Arq queue + cron)]

Browser -->|HTTPS|Dashboard
Dashboard -->|fetch JSON|API
User -->|HTTPS|API

Worker -->|IMAP SEARCH/UID FETCH|IMAP
Worker -->|signed POST|YourApp
Worker <-->|read/write|PostgreSQL
Worker <-->|enqueue/consume| Redis
API <-->|read/write|PostgreSQL
API <-->|enqueue|Redis
```

### Email-to-Webhook Flow

```mermaid
sequenceDiagram
    autonumber
    participant W as Arq worker
    participant R as Redis
    participant IMAP as IMAP server
    participant DB as PostgreSQL
    participant WH as Your webhook endpoint
    Note over W: cron fires (every 60s)
    W ->> R: dequeue monitor_mailboxes
    W ->> DB: load enabled mailboxes
    loop per mailbox
        W ->> IMAP: SEARCH UNSEEN
        IMAP -->> W: list of UIDs
        loop per unseen UID
            W ->> R: enqueue process_email_message(uid)<br/>job_id = process-email:{mailbox}:{uid}
        end
    end

    W ->> R: dequeue process_email_message
    W ->> IMAP: UID FETCH (RFC822)
    IMAP -->> W: raw bytes
    W ->> W: parse MIME → EmailEvent
    W ->> DB: INSERT email_events
    W ->> IMAP: STORE \Seen flag
    W ->> R: enqueue dispatch_webhook(event_id)
    W ->> R: dequeue dispatch_webhook
    W ->> DB: load user's active webhooks
    loop per webhook
        W ->> R: enqueue deliver_webhook(delivery_id)
    end

    W ->> R: dequeue deliver_webhook
    W ->> DB: load event + webhook
    W ->> W: HMAC-SHA256 sign payload
    W ->> WH: POST signed JSON
    WH -->> W: 2xx / 4xx / 5xx / timeout
    W ->> DB: UPDATE webhook_deliveries (status, attempt, response)
    Note over W: non-2xx → schedule retry per WEBHOOK_RETRY_DELAYS_SECONDS<br/>after max attempts → dead_lettered
```

A slow or failing webhook never blocks email ingestion: parsing and saving the email completes before the dispatch job
runs, and the dispatch job only enqueues one delivery per webhook. Retry timing is database-driven (the
`retry_failed_webhook_deliveries` cron job picks up due retries each minute), so backoff survives worker restarts.

---

## Quick Start

### Prerequisites

Verify your local toolchain before cloning:

```bash
python --version    # 3.11 or 3.12
node --version      # 20 or newer (frontend only)
docker --version    # 24+
uv --version        # optional but recommended (https://docs.astral.sh/uv/)
git --version
```

You also need a running PostgreSQL 16 and Redis 7. The fastest path is the Docker Compose setup below, which provisions
both.

### Option A — Full stack via Docker Compose

```bash
git clone https://github.com/Chisa-Sichali/MailPulse.git
cd MailPulse

# Generate .env (backend) and frontend/.env.local with safe defaults.
# Idempotent — never overwrites an existing secret.
scripts/generate-env.sh        # container-mode URLs (postgres:5432, redis:6379)

docker compose up --build -d

# Health check
curl http://localhost:8080/health/system
```

Once running:

| Service    | URL                                               |
|------------|---------------------------------------------------|
| API        | http://localhost:8080                             |
| Swagger UI | http://localhost:8080/docs                        |
| ReDoc      | http://localhost:8080/redoc                       |
| Dashboard  | http://localhost:3000                             |
| PostgreSQL | `localhost:5433` (user `mailpulse` / `mailpulse`) |
| Redis      | `localhost:6379`                                  |

Migrations run automatically when the `api` and `worker` containers start (`alembic upgrade head` is in their
entrypoint).

### Option B — Backend locally, infra in Docker

Use this when you want to iterate on the API with hot reload.

```bash
# 1. Start only Postgres + Redis
docker compose up -d postgres redis

# 2. Create a Python environment and install deps (uv is recommended)
uv sync                                              # installs runtime + dev groups from uv.lock
#    Or, without uv: python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
#                   pip install -e . pytest pytest-asyncio

# 3. Write a host-mode .env (localhost URLs instead of container DNS names)
scripts/generate-env.sh --host

# 4. Apply migrations
alembic upgrade head

# 5. Run the API (terminal 1)
uvicorn app.main:app --reload --port 8080

# 6. Run the worker (terminal 2)
arq app.workers.settings.WorkerSettings
```

### Option C — Frontend only

```bash
cd frontend
npm install

# Make sure backend/.env was generated with --host, or write
# frontend/.env.local manually:
#   NEXT_PUBLIC_API_URL=http://localhost:3000
#   NEXT_PUBLIC_FASTAPI_BACKEND_URL=http://localhost:8080

npm run dev        # http://localhost:3000
```

### First API call

```bash
# Register a user → receive token pair
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"supersecret123","full_name":"You"}'
```

The full walkthrough (register → add mailbox → register webhook → receive a signed event) is in [
`docs/api.md`](docs/api.md#end-to-end-example).

---

## Documentation

Detailed guides live in [`docs/`](docs/):

| Document                                             | Purpose                                                            |
|------------------------------------------------------|--------------------------------------------------------------------|
| [docs/architecture.md](docs/architecture.md)         | System architecture, request flow, sequence diagrams.              |
| [docs/api.md](docs/api.md)                           | REST API reference (auth, mailboxes, webhooks, events, analytics). |
| [docs/authentication.md](docs/authentication.md)     | JWT + refresh token mechanics, signing, hashing.                   |
| [docs/database.md](docs/database.md)                 | Schema, models, migrations, indexes.                               |
| [docs/webhooks.md](docs/webhooks.md)                 | Webhook payload format and signature verification.                 |
| [docs/workers.md](docs/workers.md)                   | Arq job catalogue, cron schedule, retry semantics.                 |
| [docs/email-processing.md](docs/email-processing.md) | IMAP → MIME → EmailEvent pipeline.                                 |
| [docs/dashboard.md](docs/dashboard.md)               | Next.js dashboard setup and configuration.                         |
| [docs/development.md](docs/development.md)           | Local development, scripts, debugging.                             |
| [docs/deployment.md](docs/deployment.md)             | Production deployment and reverse proxy guidance.                  |
| [docs/troubleshooting.md](docs/troubleshooting.md)   | Common setup problems and fixes.                                   |

---

## Project Structure

```text
MailPulse/
├── app/                          # FastAPI backend
│   ├── api/
│   │   ├── v1/                   # /api/v1 routers: auth, mailboxes,
│   │   │                         #   webhooks, events, analytics
│   │   └── health/               # /health/system deep check
│   ├── core/
│   │   ├── config/               # pydantic-settings (env loading)
│   │   ├── security/             # JWT, password hashing, Fernet
│   │   │                         #   encryption, webhook signing
│   │   ├── exceptions/           # Domain exceptions + FastAPI handlers
│   │   ├── logging/              # Rich-based logging setup
│   │   ├── middleware/           # Request logging
│   │   └── queue.py              # Arq pool + enqueue helpers
│   ├── database/
│   │   ├── models/               # SQLAlchemy ORM: User, Mailbox,
│   │   │                         #   EmailEvent, Webhook, etc.
│   │   ├── repositories/         # Data-access objects
│   │   └── session.py            # Async engine + session factory
│   ├── schemas/                  # Pydantic request/response models
│   ├── services/                 # Business logic (auth, mailbox,
│   │                             #   webhook, email_processing, analytics)
│   ├── workers/                  # Arq task definitions and settings
│   └── main.py                   # FastAPI app factory + lifespan
├── alembic/                      # Database migrations
│   └── versions/                 # 001–004: auth, mailboxes,
│                                 #   email_events, webhooks
├── frontend/                     # Next.js 16 dashboard (App Router)
│   ├── app/                      # Routes (login + protected group)
│   ├── components/               # UI primitives (shadcn-based)
│   ├── features/                 # Feature modules (auth, dashboard,
│   │                             #   mailboxes, webhooks, events,
│   │                             #   analytics, system, infrastructure)
│   ├── services/                 # API client + auth service
│   ├── stores/                   # Zustand client stores
│   ├── config/                   # Public env config (config.ts)
│   └── Dockerfile                # Three-stage Next.js production image
├── tests/                        # pytest-asyncio suite
├── docs/                         # Long-form documentation (see above)
├── scripts/
│   └── generate-env.sh           # Idempotent .env generator
├── docker-compose.yml            # postgres + redis + api + worker + dashboard
├── Dockerfile                    # uv-based backend image
├── pyproject.toml                # uv-managed Python dependencies
├── uv.lock                       # Pinned dependency lockfile
├── alembic.ini                   # Alembic configuration
├── pytest.ini                    # pytest configuration
├── .env.example                  # Backend env template
├── LICENSE                       # MIT
└── README.md                     # This file
```

---

## Technology Stack

| Layer            | Technology                       | Purpose                                                      |
|------------------|----------------------------------|--------------------------------------------------------------|
| Backend runtime  | Python 3.11                      | Async-first language with a mature IMAP/HTTP ecosystem.      |
| API framework    | FastAPI 0.128                    | Type-driven REST framework with auto OpenAPI.                |
| ASGI server      | Uvicorn                          | Production HTTP server.                                      |
| Data validation  | Pydantic v2 / pydantic-settings  | Request/response models, env loading.                        |
| ORM              | SQLAlchemy 2 (async)             | Async ORM with `asyncpg`.                                    |
| Migrations       | Alembic                          | Versioned schema migrations.                                 |
| Database         | PostgreSQL 16                    | System of record.                                            |
| Job queue        | Arq 0.26                         | Async Redis-backed job runner with cron.                     |
| Cache / broker   | Redis 7                          | Arq broker + future cache use.                               |
| JWT / password   | `python-jose`, `passlib[bcrypt]` | HS256 JWTs, bcrypt password hashing.                         |
| Encryption       | `cryptography` (Fernet)          | At-rest encryption of mailbox passwords and webhook secrets. |
| HTTP client      | `httpx`                          | Outbound webhook delivery.                                   |
| MIME parsing     | `email-reply-parser`             | Reply-thread detection.                                      |
| Logging          | `rich`                           | Pretty console logging in dev.                               |
| Dependency mgmt  | `uv`                             | Reproducible Python environments with locked deps.           |
| Containerisation | Docker, Docker Compose           | Reproducible dev and deploy.                                 |
| Frontend         | Next.js 16 (App Router)          | React-based management UI.                                   |
| UI components    | shadcn/ui + Tailwind v4          | Composable, themeable primitives.                            |
| Data fetching    | TanStack Query v5                | Caching, refetching, mutations on the client.                |
| Charts           | Recharts                         | Volume + performance charts.                                 |
| State            | Zustand                          | Lightweight client stores.                                   |
| Frontend linting | ESLint 9 + `eslint-config-next`  | Next.js + TypeScript lint rules.                             |
| Backend testing  | pytest, pytest-asyncio           | Async test suite against a test database.                    |

---

## Environment Variables

The backend reads its configuration from a `.env` file at the project root via
`pydantic-settings`. The frontend reads `NEXT_PUBLIC_*` variables from
`frontend/.env.local` (created automatically by `scripts/generate-env.sh`).

### Backend (`.env`)

| Variable                              | Required | Default                                                                       | Description                                                                                                                                                                                                                                   |
|---------------------------------------|----------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `APP_NAME`                            | no       | `MailPulse`                                                                   | Service name reported in `/health/system`.                                                                                                                                                                                                    |
| `APP_VERSION`                         | no       | `0.1.0`                                                                       | Service version (override in CI/CD).                                                                                                                                                                                                          |
| `ENVIRONMENT`                         | no       | `development`                                                                 | Free-form environment label (e.g. `staging`, `production`).                                                                                                                                                                                   |
| `DEBUG`                               | no       | `false`                                                                       | Debug flag for verbose logs.                                                                                                                                                                                                                  |
| `DATABASE_URL`                        | **yes**  | `postgresql+asyncpg://mailpulse:mailpulse@localhost:5433/mailpulse`           | Async SQLAlchemy DSN.                                                                                                                                                                                                                         |
| `REDIS_URL`                           | **yes**  | `redis://localhost:6379/0`                                                    | Redis DSN used by Arq.                                                                                                                                                                                                                        |
| `JWT_SECRET_KEY`                      | **yes**  | `change-me-in-production`                                                     | HMAC secret for signing access tokens. Set to a long random value in prod.                                                                                                                                                                    |
| `CREDENTIAL_ENCRYPTION_KEY`           | **yes**  | *(empty)*                                                                     | Fernet key for mailbox/webhook secret encryption. If unset, the encryption layer falls back to `JWT_SECRET_KEY` — so for production you should set a distinct value (and back it up: losing this key permanently bricks every encrypted row). |
| `CRON_SECRET_KEY`                     | no       | *(empty)*                                                                     | Bearer token for cron-protected routes (reserved; no route uses it yet).                                                                                                                                                                      |
| `JWT_ALGORITHM`                       | no       | `HS256`                                                                       | JWT signing algorithm.                                                                                                                                                                                                                        |
| `ACCESS_TOKEN_EXPIRE_MINUTES`         | no       | `30`                                                                          | Access token lifetime.                                                                                                                                                                                                                        |
| `REFRESH_TOKEN_EXPIRE_DAYS`           | no       | `7`                                                                           | Refresh token lifetime.                                                                                                                                                                                                                       |
| `EMAIL_MONITOR_POLL_INTERVAL_SECONDS` | no       | `60` (min 30)                                                                 | How often the worker scans mailboxes.                                                                                                                                                                                                         |
| `ARQ_MAX_TRIES`                       | no       | `4`                                                                           | Max retries per Arq job before it fails terminally.                                                                                                                                                                                           |
| `ARQ_JOB_TIMEOUT`                     | no       | `300`                                                                         | Per-job timeout in seconds.                                                                                                                                                                                                                   |
| `WEBHOOK_MAX_ATTEMPTS`                | no       | `4`                                                                           | Max webhook delivery attempts before dead-lettering.                                                                                                                                                                                          |
| `WEBHOOK_RETRY_DELAYS_SECONDS`        | no       | `[60, 300, 1800, 7200]`                                                       | Backoff schedule between delivery attempts.                                                                                                                                                                                                   |
| `CORS_ORIGINS`                        | no       | `["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]` | Allowed browser origins.                                                                                                                                                                                                                      |

> **Important:** `JWT_SECRET_KEY` and `CREDENTIAL_ENCRYPTION_KEY` MUST be
> replaced with strong random values before any deployment outside local
> development. The Fernet key in particular is derived into the actual
> encryption key — losing it permanently bricks every encrypted row.

### Frontend (`frontend/.env.local`)

| Variable                          | Required | Default                 | Description                                               |
|-----------------------------------|----------|-------------------------|-----------------------------------------------------------|
| `NEXT_PUBLIC_API_URL`             | no       | `http://localhost:3000` | Public base URL of the dashboard itself (used for links). |
| `NEXT_PUBLIC_FASTAPI_BACKEND_URL` | **yes**  | `http://localhost:8000` | Base URL the browser uses to reach the FastAPI backend.   |

`NEXT_PUBLIC_*` values are inlined into the client bundle at build time by Next.js, so changing them requires a rebuild.

---

## API

All endpoints are mounted under the `/api/v1` prefix. Authenticated routes require an
`Authorization: Bearer <access_token>` header.

Interactive documentation is auto-generated by FastAPI:

| URL                                  | Description                            |
|--------------------------------------|----------------------------------------|
| `http://localhost:8080/docs`         | Swagger UI — try every endpoint live.  |
| `http://localhost:8080/redoc`        | ReDoc — read-only reference rendering. |
| `http://localhost:8080/openapi.json` | Raw OpenAPI 3 schema.                  |

The complete endpoint catalogue (request/response shapes, status codes, pagination) is in [`docs/api.md`](docs/api.md).
High-level groups:

| Group     | Endpoints                                                    |
|-----------|--------------------------------------------------------------|
| Auth      | `register`, `login`, `refresh`, `logout`, `me`               |
| Mailboxes | CRUD + `test-connection`                                     |
| Webhooks  | CRUD + `rotate-secret`, `test`, list deliveries              |
| Events    | list / get + `retry`                                         |
| Analytics | `overview`, `top-senders`, `volume`, `webhooks`, `resources` |
| Health    | `/`, `/health/ready`, `/health/system`                       |

---

## Authentication

MailPulse uses two token types:

- **Access token** — HS256-signed JWT carrying the user UUID in the `sub`
  claim, with a `type: "access"` discriminator and a 30-minute expiry by default. Sent in `Authorization: Bearer …`.
- **Refresh token** — opaque, cryptographically random, 48-byte URL-safe string. Stored in PostgreSQL as a SHA-256 hash,
  with an expiry and a nullable `revoked_at`. 7-day lifetime by default.

The full auth flow (register → token pair → refresh rotation → logout revocation → password hashing → Fernet encryption
of secrets) is documented in [`docs/authentication.md`](docs/authentication.md).

Webhook payloads are signed independently — see
[`docs/webhooks.md`](docs/webhooks.md#signature-verification).

---

## Background Workers & Retries

The Arq worker (`app/workers/settings.py`) runs five functions:

| Function                          | Trigger                        | Purpose                                               |
|-----------------------------------|--------------------------------|-------------------------------------------------------|
| `monitor_mailboxes`               | cron, every 60s (configurable) | Poll all enabled mailboxes; enqueue per-email jobs.   |
| `process_email_message`           | per unseen UID                 | Fetch RFC822, parse, save `EmailEvent`, mark `\Seen`. |
| `dispatch_webhook`                | per saved event                | Fan out to the user's enabled webhooks.               |
| `deliver_webhook`                 | per delivery                   | Sign + POST payload, record status.                   |
| `retry_failed_webhook_deliveries` | cron, every minute             | Re-queue deliveries whose `next_retry_at` is due.     |

Webhook deliveries retry with the configured backoff (`WEBHOOK_RETRY_DELAYS_SECONDS`, default `60s → 5m → 30m → 2h`).
After
`WEBHOOK_MAX_ATTEMPTS` failed attempts the delivery is marked
`dead_lettered` and no longer auto-retried; re-queue it via
`POST /api/v1/events/{id}/retry`.

Deduplication job IDs (`process-email:{mailbox}:{uid}`, etc.) prevent the same email from being processed twice if the
worker restarts mid-batch.

Full reference: [`docs/workers.md`](docs/workers.md).

---

## Testing

```bash
# From the repository root
pytest                       # full async suite
pytest tests/test_auth.py    # single file
pytest -k webhook            # by keyword
```

Tests use a separate database (`TEST_DATABASE_URL`, default
`postgresql+asyncpg://mailpulse:mailpulse@localhost:5433/mailpulse_test`)
and create/drop the schema per session via SQLAlchemy metadata. The Postgres and Redis services must be reachable; the
simplest way is to start them via Docker Compose:

```bash
docker compose up -d postgres redis
pytest
```

The frontend has no test suite today. Linting is the only check — see below.

---

## Linting & Formatting

### Backend

`pyproject.toml` configures `black` (line length 88). Ruff, mypy, and similar tools are not configured; follow the
existing code style (type hints on public functions, snake_case modules, async-first).

There is no separate lint command — `pytest` is the canonical check.

### Frontend

```bash
cd frontend
npm run lint
```

This runs ESLint with `eslint-config-next` (Core Web Vitals + TypeScript rules). Prettier is configured for formatting
via the Tailwind plugin.

---

## Deployment

The Docker Compose file in this repo is the simplest deployment: it runs the API, worker, dashboard, Postgres, and Redis
in a single host with a shared network. It is suitable for:

- Self-hosted single-node deployments
- Staging environments
- Demo / evaluation setups

For production, see [`docs/deployment.md`](docs/deployment.md), which covers:

- Generating strong secrets with `scripts/generate-env.sh`
- Fronting the API and dashboard with a reverse proxy (Nginx, Traefik, Caddy)
  for TLS termination
- Externalising the database and Redis for durability and scaling
- Mounting persistent volumes for Postgres

No managed-service deployment manifests (AWS App Runner, Fly, Render, etc.)
are included in this repository today.

---

## Troubleshooting

Common local setup issues:

| Symptom                                            | Likely cause                                               | Fix                                                                                   |
|----------------------------------------------------|------------------------------------------------------------|---------------------------------------------------------------------------------------|
| `connection refused` on Postgres at boot           | Postgres container not healthy yet                         | Wait for `docker compose ps` to show `postgres` healthy, then retry.                  |
| `relation does not exist` errors from the API      | Migrations not applied                                     | Run `alembic upgrade head` (local) or `docker compose restart api worker`.            |
| Webhook deliveries stuck `pending`                 | Worker process not running                                 | Start the worker: `arq app.workers.settings.WorkerSettings`.                          |
| `403 Invalid or unauthorized cron token`           | `CRON_SECRET_KEY` mismatch                                 | Regenerate with `scripts/generate-env.sh`; never edit the env file mid-deploy.        |
| `Failed to decrypt mailbox credentials` on connect | `CREDENTIAL_ENCRYPTION_KEY` changed or was empty on insert | Re-add the original mailbox or rotate by re-creating it via `POST /mailboxes`.        |
| Dashboard shows `Network Error`                    | `NEXT_PUBLIC_FASTAPI_BACKEND_URL` wrong, or CORS           | Confirm env var, restart `npm run dev`, and that the API origin is in `CORS_ORIGINS`. |
| `Address already in use` on port 8080              | Another process bound to the port                          | `lsof -i :8080` / `netstat -ano \| findstr :8080`, kill the PID, retry.               |
| `npm install` fails on Apple Silicon               | `libc6-compat` missing                                     | Already handled by `frontend/Dockerfile`; locally, `brew install libc6-compat`.       |

See [`docs/troubleshooting.md`](docs/troubleshooting.md) for more.

---

## Contributing

1. Fork and clone the repository.
2. Create a feature branch (`git checkout -b feature/my-change`).
3. Set up a local environment with `scripts/generate-env.sh --host` and
   `docker compose up -d postgres redis`.
4. Make changes. Follow the existing layering:
    - HTTP handlers belong in `app/api/v1/`.
    - Business logic in `app/services/`.
    - Data access in `app/database/repositories/`.
    - Pydantic models in `app/schemas/`.
    - Background jobs in `app/workers/`.
    - Frontend feature code under `frontend/features/<feature>/`.
5. Add or update tests in `tests/` for any backend change.
6. Run `pytest` and `cd frontend && npm run lint`.
7. Open a pull request with a clear summary of the change and the user-visible impact.

There is no formal CODEOWNERS, contribution license agreement, or required commit-message format in this repository.

---

## License

[MIT](LICENSE) — see the `LICENSE` file for the full text.
