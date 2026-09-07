# Database

MailPulse uses PostgreSQL 16 with the `pgcrypto` UUID generator and JSONB for
flexible columns. The schema is managed exclusively by Alembic — there is no
ad-hoc `CREATE TABLE` outside migrations.

## Engines and connection

- **Driver:** `asyncpg` via SQLAlchemy 2 (async).
- **DSN:** `DATABASE_URL` (default `postgresql+asyncpg://mailpulse:mailpulse@localhost:5433/mailpulse`).
- **Pool:** `pool_size=20`, `max_overflow=10` (see `app/database/session.py`).
- **Time zone:** all `DateTime` columns are timezone-aware.

The async engine is created at import time, so any module that imports
`app.database.session` must do so after `Settings()` is initialised. In
practice, the engine is a singleton consumed via `get_engine`,
`get_session_factory`, and the `get_db_session` FastAPI dependency.

## Migrations

```bash
# apply all pending migrations
alembic upgrade head

# roll back the last migration
alembic downgrade -1

# generate a new migration from model changes
alembic revision --autogenerate -m "describe the change"

# create an empty migration (for data backfills, etc.)
alembic revision -m "describe the change"
```

`alembic/env.py` reads `DATABASE_URL` from settings, so no manual `.ini`
editing is needed. `target_metadata` is `Base.metadata` (from
`app.database.models`).

Migrations in `alembic/versions/`:

| File                          | Adds                                              |
| ----------------------------- | ------------------------------------------------- |
| `001_initial_auth.py`         | `users`, `refresh_tokens`                         |
| `002_add_mailboxes.py`        | `mailboxes`                                       |
| `003_add_email_events.py`     | `email_events`                                    |
| `004_add_webhooks.py`         | `webhooks`, `webhook_deliveries`                  |

Docker Compose runs `alembic upgrade head` on container start for both `api`
and `worker`. For local dev, run it manually after `uv sync`.

## Schema overview

```mermaid
erDiagram
    users ||--o{ refresh_tokens : has
    users ||--o{ mailboxes : owns
    users ||--o{ webhooks : owns
    mailboxes ||--o{ email_events : receives
    webhooks ||--o{ webhook_deliveries : "delivers via"
    email_events ||--o{ webhook_deliveries : "delivered by"

    users {
        uuid id PK
        string email
        string password_hash
        string full_name
        bool is_active
        bool is_verified
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }
    refresh_tokens {
        uuid id PK
        uuid user_id FK
        string token_hash
        timestamp expires_at
        timestamp revoked_at
        timestamp created_at
    }
    mailboxes {
        uuid id PK
        uuid user_id FK
        string email_address
        string imap_username
        string imap_host
        int imap_port
        text encrypted_password
        bool is_enabled
        string health_status
        timestamp last_sync_at
        timestamp last_error_at
        text last_error_message
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }
    email_events {
        uuid id PK
        uuid mailbox_id FK
        string message_id
        string imap_uid
        string sender_email
        string sender_name
        jsonb recipients
        text subject
        text text_body
        text html_body
        jsonb attachments_metadata
        string in_reply_to
        string status
        text error_message
        int attempt_count
        timestamp received_at
        timestamp processed_at
        timestamp created_at
        timestamp updated_at
    }
    webhooks {
        uuid id PK
        uuid user_id FK
        string url
        string name
        text encrypted_secret
        string secret_prefix
        bool is_enabled
        jsonb event_types
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }
    webhook_deliveries {
        uuid id PK
        uuid webhook_id FK
        uuid email_event_id FK
        string status
        int attempt_count
        int http_status_code
        text response_body
        timestamp next_retry_at
        timestamp delivered_at
        text last_error
        timestamp created_at
        timestamp updated_at
    }
```

## Models

### `users`

| Column           | Type                 | Notes                                                          |
| ---------------- | -------------------- | -------------------------------------------------------------- |
| `id`             | UUID PK              | `uuid.uuid4()` default.                                        |
| `email`          | VARCHAR(255)         | Unique, indexed.                                               |
| `password_hash`  | VARCHAR(255)         | bcrypt via passlib.                                            |
| `full_name`      | VARCHAR(255) NULL    | Optional.                                                      |
| `is_active`      | BOOL                 | Server default `true`.                                         |
| `is_verified`    | BOOL                 | Server default `false`. Verification flow not implemented.     |
| `created_at`     | TIMESTAMPTZ          | Server default `now()`.                                        |
| `updated_at`     | TIMESTAMPTZ          | Server default + `onupdate`.                                   |
| `deleted_at`     | TIMESTAMPTZ NULL     | Soft-delete column, indexed. Unused at the API layer today.    |

Relationships: `mailboxes`, `webhooks`, `refresh_tokens` (all `delete-orphan`).

### `refresh_tokens`

| Column        | Type         | Notes                                                            |
| ------------- | ------------ | ---------------------------------------------------------------- |
| `id`          | UUID PK      |                                                                  |
| `user_id`     | UUID FK      | `users.id`, `ON DELETE CASCADE`.                                 |
| `token_hash`  | VARCHAR(64)  | SHA-256 hex of the raw token. Unique, indexed.                   |
| `expires_at`  | TIMESTAMPTZ  | `now() + REFRESH_TOKEN_EXPIRE_DAYS`.                             |
| `revoked_at`  | TIMESTAMPTZ  | Nullable. Set on rotation/logout.                                |
| `created_at`  | TIMESTAMPTZ  |                                                                  |
| `updated_at`  | TIMESTAMPTZ  |                                                                  |

Property: `is_revoked` returns `revoked_at is not None`.

### `mailboxes`

| Column                | Type            | Notes                                                            |
| --------------------- | --------------- | ---------------------------------------------------------------- |
| `id`                  | UUID PK         |                                                                  |
| `user_id`             | UUID FK         | `users.id`, `ON DELETE CASCADE`. Indexed.                        |
| `email_address`       | VARCHAR(255)    |                                                                  |
| `imap_username`       | VARCHAR(255)    | Usually `email_address`; configurable.                          |
| `imap_host`           | VARCHAR(255)    |                                                                  |
| `imap_port`           | INT             | Server default `993`.                                            |
| `encrypted_password`  | TEXT            | Fernet ciphertext of the IMAP password.                          |
| `is_enabled`          | BOOL            | Server default `true`. Disabled mailboxes are skipped by polling.|
| `health_status`       | VARCHAR(32)     | One of `healthy`, `degraded`, `error`, `unknown`. Server default `unknown`. |
| `last_sync_at`        | TIMESTAMPTZ     | Set by the worker after each successful sweep.                   |
| `last_error_at`       | TIMESTAMPTZ     | Set when the worker hits a connectivity error.                   |
| `last_error_message`  | TEXT            | Last error string.                                               |
| `created_at` / `updated_at` | TIMESTAMPTZ |                                                                  |
| `deleted_at`          | TIMESTAMPTZ     | Soft-delete column; worker filters on `deleted_at IS NULL`.      |

### `email_events`

| Column                  | Type            | Notes                                                            |
| ----------------------- | --------------- | ---------------------------------------------------------------- |
| `id`                    | UUID PK         |                                                                  |
| `mailbox_id`            | UUID FK         | `mailboxes.id`, `ON DELETE CASCADE`.                             |
| `message_id`            | VARCHAR(512)    | RFC822 `Message-ID` header.                                      |
| `imap_uid`              | VARCHAR(64)     | IMAP UID (for dedup).                                            |
| `sender_email`          | VARCHAR(255)    |                                                                  |
| `sender_name`           | VARCHAR(255)    | Server default `''`.                                             |
| `recipients`            | JSONB           | Array of recipient strings. Server default `'[]'::jsonb`.        |
| `subject`               | TEXT            | Server default `''`.                                             |
| `text_body`             | TEXT            | Plain-text body (charset-normalised).                            |
| `html_body`             | TEXT            | HTML body (charset-normalised).                                  |
| `attachments_metadata`  | JSONB           | Array of `{filename, content_type, size}`.                       |
| `in_reply_to`           | VARCHAR(512)    | RFC822 `In-Reply-To` header, if present.                         |
| `status`                | VARCHAR(32)     | `pending` | `delivered` | `failed` | `dead_lettered`.           |
| `error_message`         | TEXT            | Set on parse failures.                                           |
| `attempt_count`         | INT             | Server default `0`.                                              |
| `received_at`           | TIMESTAMPTZ     | From the `Date` header.                                          |
| `processed_at`          | TIMESTAMPTZ     | Set when the parser finishes.                                    |
| `created_at` / `updated_at` | TIMESTAMPTZ |                                                                  |

### `webhooks`

| Column            | Type            | Notes                                                            |
| ----------------- | --------------- | ---------------------------------------------------------------- |
| `id`              | UUID PK         |                                                                  |
| `user_id`         | UUID FK         | `users.id`, `ON DELETE CASCADE`. Indexed.                        |
| `url`             | VARCHAR(2048)   |                                                                  |
| `name`            | VARCHAR(255)    | Optional.                                                        |
| `encrypted_secret`| TEXT            | Fernet ciphertext of the signing secret.                        |
| `secret_prefix`   | VARCHAR(16)     | First ~12 chars of `secret` (display only, never used for signing). |
| `is_enabled`      | BOOL            | Server default `true`.                                           |
| `event_types`     | JSONB           | Default `["email.received"]`.                                   |
| `created_at` / `updated_at` | TIMESTAMPTZ |                                                              |
| `deleted_at`      | TIMESTAMPTZ     | Soft-delete column, indexed. The current code hard-deletes via the API; the column is reserved. |

### `webhook_deliveries`

| Column            | Type            | Notes                                                            |
| ----------------- | --------------- | ---------------------------------------------------------------- |
| `id`              | UUID PK         |                                                                  |
| `webhook_id`      | UUID FK         | `webhooks.id`, `ON DELETE CASCADE`.                             |
| `email_event_id`  | UUID FK         | `email_events.id`, `ON DELETE CASCADE`. Indexed.                 |
| `status`          | VARCHAR(32)     | `pending` | `delivered` | `failed` | `dead_lettered`.          |
| `attempt_count`   | INT             | Server default `0`.                                              |
| `http_status_code`| INT NULL        | From the last delivery attempt.                                  |
| `response_body`   | TEXT NULL       | Truncated response from the destination.                         |
| `next_retry_at`   | TIMESTAMPTZ     | When the retry cron should re-enqueue this row.                  |
| `delivered_at`    | TIMESTAMPTZ     | Set when status flips to `delivered`.                            |
| `last_error`      | TEXT            | Exception text from the last failed attempt.                     |
| `created_at` / `updated_at` | TIMESTAMPTZ |                                                              |

## Indexes

- `users.email` — unique
- `users.deleted_at` — b-tree
- `refresh_tokens.user_id`, `refresh_tokens.token_hash` — unique
- `mailboxes.user_id`, `mailboxes.deleted_at` — b-tree
- `email_events.mailbox_id`, `email_events` implicit FK indexes
- `webhooks.user_id`, `webhooks.deleted_at` — b-tree
- `webhook_deliveries.email_event_id`, FK indexes on `webhook_id`

## Repository layer

`app/database/repositories/` wraps the models and is the only place that
runs queries. Routes never touch SQLAlchemy directly; services never write
SQL by hand.

| Repository                  | Owns                                         |
| --------------------------- | -------------------------------------------- |
| `UserRepository`            | `User`                                        |
| `RefreshTokenRepository`    | `RefreshToken`                                |
| `MailboxRepository`         | `Mailbox` (including soft-delete filtering)  |
| `EmailEventRepository`      | `EmailEvent`                                  |
| `WebhookRepository`         | `Webhook`                                     |
| `WebhookDeliveryRepository` | `WebhookDelivery`                             |
| `AnalyticsRepository`       | Read-only aggregations over `email_events` and `webhook_deliveries`. |

## Reset / re-create

To drop and recreate the database (DESTRUCTIVE):

```bash
docker compose down -v          # remove Postgres volume
docker compose up -d postgres
docker compose run --rm api alembic upgrade head
```

For a soft reset that keeps the schema but clears data:

```sql
TRUNCATE webhook_deliveries, email_events, webhooks,
         mailboxes, refresh_tokens, users RESTART IDENTITY CASCADE;
```

## Test database

`tests/conftest.py` uses `TEST_DATABASE_URL` (default
`postgresql+asyncpg://mailpulse:mailpulse@localhost:5433/mailpulse_test`).
It calls `Base.metadata.create_all` once per session and `drop_all` on
teardown, so migrations are not exercised by the test suite — schemas come
from the live models.

To run tests against a separate Postgres instance, export the variable
before invoking pytest:

```bash
TEST_DATABASE_URL=postgresql+asyncpg://… pytest
```
