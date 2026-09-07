# Troubleshooting

Common issues and how to fix them. Most are environment-setup problems;
once the stack is running, MailPulse is largely self-correcting.

## Docker / infrastructure

### `docker compose up` fails: "port is already allocated"

A previous compose stack, a system Postgres, or a stray process is using
the host port.

```bash
# Find what is listening on the conflicting port (Linux / macOS)
lsof -i :5433
lsof -i :6379
lsof -i :8080
lsof -i :3000

# Windows (PowerShell)
Get-NetTCPConnection -LocalPort 5433
```

Stop the conflicting process, or change the host port in
`docker-compose.yml` (e.g. `"5434:5432"` for Postgres).

### Postgres container exits immediately

Almost always a permissions issue with the named volume. Reset:

```bash
docker compose down -v          # DESTRUCTIVE — drops Postgres data
docker compose up -d postgres
docker compose run --rm api alembic upgrade head
```

### Redis healthcheck fails

```bash
docker compose logs redis
```

If you see `NOAUTH Authentication required`, your `REDIS_URL` includes a
password that the bundled Redis doesn't have. Either remove the password
or run a separate Redis with auth enabled.

## API

### `relation "users" does not exist`

Migrations were not applied. Run:

```bash
alembic upgrade head                  # local dev
docker compose restart api worker     # containerised
```

### `503 Service Unavailable` from `/health/system`

The deep health check returns 503 only when the API cannot reach Postgres
or Redis. The response body explains which:

```json
{ "checks": { "database": "error: …", "redis": "connected" }, "status": "degraded" }
```

Investigate whichever check failed. In a fresh container, this is almost
always a wrong host in `DATABASE_URL` or `REDIS_URL` — for local dev,
`localhost:5433` (Postgres) and `localhost:6379` (Redis); inside Docker
Compose, `postgres:5432` and `redis:6379`.

### `401 Unauthorized` immediately after login

The access token has expired or the dashboard's localStorage was cleared.
The dashboard's `apiFetch` should auto-refresh; if it doesn't, open
`/health/system` to confirm the API is reachable, then check
`CORS_ORIGINS` for the dashboard origin.

If you see `Invalid or expired access token` from `get_current_user`,
the token may have been issued by a different `JWT_SECRET_KEY` (the env
var changed since the user logged in). Have the user log in again.

### `403 Invalid or unauthorized cron token`

The `verify_cron_request` dependency in `app/core/security/cron.py` is
wired up but no production route uses it today. If you see this error, a
caller is hitting a future cron endpoint without the right
`CRON_SECRET_KEY`. Generate or rotate it with `scripts/generate-env.sh`.

## Worker

### Webhook deliveries stuck on `pending`

The worker is not running. Start it:

```bash
arq app.workers.settings.WorkerSettings
# or, in Docker Compose:
docker compose up -d worker
```

You can also see whether jobs are queued in Redis:

```bash
docker compose exec redis redis-cli LLEN arq:queue
```

### `deliver_webhook` job times out

`ARQ_JOB_TIMEOUT` (default 300 seconds) is exceeded. Either:

- Slow webhook endpoint → raise `ARQ_JOB_TIMEOUT` (note: raising it
  affects every job).
- Slow webhook endpoint → fix the endpoint; it should respond within a
  couple of seconds and process asynchronously.
- Genuine network issue → check the destination is reachable from the
  worker container:

  ```bash
  docker compose exec worker curl -I https://myapp.com/hooks/email
  ```

### Mailboxes never get events

1. Confirm the worker is running (above).
2. Confirm the mailbox is `enabled` and not soft-deleted
   (`GET /api/v1/mailboxes`).
3. Run `POST /api/v1/mailboxes/{id}/test-connection` to validate IMAP
   credentials. Many providers require an **app password**, not the
   account password.
4. Confirm `EMAIL_MONITOR_POLL_INTERVAL_SECONDS` is set to something
   reasonable (default 60 seconds).
5. Check worker logs for IMAP errors:

   ```bash
   docker compose logs worker | grep -i imap
   ```

## Encryption

### `Failed to decrypt mailbox credentials`

`CREDENTIAL_ENCRYPTION_KEY` is wrong or changed since the row was
encrypted. Fernet decryption is unforgiving — even a one-character
difference throws `InvalidToken`.

Recovery options:

- Restore the original key value in `.env` (or your secrets manager) and
  restart.
- If the original key is unrecoverable, the affected rows must be
  deleted; they cannot be decrypted. Add a new mailbox with the new
  credentials via `POST /api/v1/mailboxes`.

> This is by design. Always back up
> `CREDENTIAL_ENCRYPTION_KEY` (and `JWT_SECRET_KEY`) with the same
> rigour as your database backups.

## Frontend

### `Network Error` in the dashboard

1. `NEXT_PUBLIC_FASTAPI_BACKEND_URL` is wrong. Open
   `frontend/.env.local` and verify the value.
2. The backend is not reachable from the browser. If you started the
   API on `localhost:8080` but the dashboard is in a container on a
   different network, the URL must be `http://api:8080`, not
   `http://localhost:8080`.
3. CORS: the API must list the dashboard origin in `CORS_ORIGINS`.

`npm run dev` reads `.env.local` on (re)start — restart it after edits.

### `npm install` fails on Apple Silicon

```text
ld: warning: … searching for undefined symbols in libc6-compat
```

The containerised `frontend/Dockerfile` already installs
`libc6-compat`; locally, install it via Homebrew:

```bash
brew install libc6-compat
```

### Dashboard builds but pages render blank

Almost always a runtime error swallowed by React. Open the browser
devtools console — usually a TanStack Query error or a hydration
mismatch.

Common causes:

- Stale TanStack Query cache after a schema change — clear the cache:
  open devtools and run
  `window.localStorage.clear(); window.location.reload();`
- A new shadcn primitive was added without updating `components/ui/`'s
  imports — re-run the `shadcn add` command from the project root.

## Tests

### `pytest` errors with `connection refused` to Postgres

```bash
docker compose up -d postgres redis
pytest
```

### `pytest` errors with `password authentication failed`

`TEST_DATABASE_URL` does not match the running Postgres credentials.
The default is
`postgresql+asyncpg://mailpulse:mailpulse@localhost:5433/mailpulse_test`;
override with:

```bash
TEST_DATABASE_URL=postgresql+asyncpg://mailpulse:mailpulse@localhost:5433/mailpulse_test pytest
```

### `pytest` errors with `SAWarning: … relationship … will copy column`

Cosmetic. The test database is created from SQLAlchemy metadata
(`Base.metadata.create_all` in `tests/conftest.py`) and does not enforce
the same index names as the Alembic migrations. Safe to ignore during
tests, but the warning will not appear in production because production
uses Alembic.

## Reset everything

If nothing else works and you want a clean slate (DESTRUCTIVE — drops the
Postgres data volume):

```bash
docker compose down -v
docker compose up -d postgres redis
scripts/generate-env.sh --host
uv sync
alembic upgrade head
```
