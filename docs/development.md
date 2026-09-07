# Development

This page covers the day-to-day workflow for running MailPulse locally and
contributing to the backend or the dashboard.

If you only want to evaluate the system end-to-end, the
[README quick start](../README.md#quick-start) is the shorter path.

## Prerequisites

Verify the toolchain once before you start:

```bash
python --version    # 3.11 or 3.12
node --version      # 20+ (frontend only)
docker --version    # 24+
uv --version        # recommended for Python deps
git --version
```

`uv` is the recommended way to manage the Python environment — the repo
includes a `uv.lock` so installs are deterministic. Without uv, create a
venv and install runtime + test deps manually:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
pip install pytest pytest-asyncio
```

## First-time setup

```bash
# 1. Clone
git clone https://github.com/Chisa-Sichali/MailPulse.git
cd MailPulse

# 2. Start Postgres + Redis
docker compose up -d postgres redis

# 3. Write a host-mode .env (localhost URLs)
scripts/generate-env.sh --host

# 4. Install backend deps with uv
uv sync

# 5. Apply migrations
alembic upgrade head

# 6. Run API + worker (separate terminals)
uvicorn app.main:app --reload --port 8080
arq app.workers.settings.WorkerSettings
```

Then in another terminal:

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

You should now have all five processes running: Postgres, Redis, API,
worker, and the dashboard.

## `scripts/generate-env.sh`

This is the only supported way to populate `.env` and
`frontend/.env.local`. It is **idempotent** — running it again does not
overwrite an existing secret.

```bash
scripts/generate-env.sh            # container mode (defaults)
scripts/generate-env.sh --host     # host mode (localhost URLs for uvicorn + npm)
```

What it does:

- Generates `JWT_SECRET_KEY` (random base64), `CRON_SECRET_KEY` (random
  hex), and `CREDENTIAL_ENCRYPTION_KEY` (random base64) only if missing or
  still set to a placeholder.
- Sets `DATABASE_URL` and `REDIS_URL` based on the mode flag.
- Writes `frontend/.env.local` with the right
  `NEXT_PUBLIC_FASTAPI_BACKEND_URL` for the mode.
- Refuses to write inside a runtime container unless `ENV_GEN_ALLOWED=1`
  (the `env-gen` service in `docker-compose.yml` sets this).

## Day-to-day commands

```bash
# Backend
uv sync                            # update / install Python deps
uvicorn app.main:app --reload --port 8080
arq app.workers.settings.WorkerSettings
alembic upgrade head               # apply pending migrations
alembic revision --autogenerate -m "describe change"
alembic downgrade -1               # roll back last migration
pytest                             # run the test suite
pytest tests/test_auth.py          # single file
pytest -k webhook                  # by keyword

# Frontend
cd frontend
npm install
npm run dev                        # dev server
npm run build                      # production build
npm start                          # run production build locally
npm run lint                       # ESLint

# Infrastructure
docker compose up -d postgres redis
docker compose down                # stop everything
docker compose down -v             # stop + drop volumes (DESTRUCTIVE)
docker compose logs -f api worker  # tail logs
```

## Codebase conventions

- Python: type hints on all public functions; async-first; one module per
  service area.
- Layering: `api → services → repositories → models`. Each layer only
  imports the layer immediately below it.
- Schemas: Pydantic v2 with `model_config = ConfigDict(from_attributes=True)`
  on response models so they can be built from ORM rows.
- Errors: subclass `MailPulseError` from `app/core/exceptions/base.py` and
  register a handler in `app/core/exceptions/handlers.py`.
- Frontend: prefer Server Components; mark Client Components with
  `"use client"`; use `apiFetch` from `frontend/services/api-client.ts`
  for every backend call.

## Where to make changes

| You want to…              | Edit                                                      |
| ------------------------- | --------------------------------------------------------- |
| Add an API endpoint       | `app/api/v1/<area>/routes.py` + `app/schemas/<area>.py` + `app/services/<area>/<service>.py` |
| Change validation         | `app/schemas/<area>.py`                                   |
| Add a database column     | Add column to `app/database/models/<model>.py` + new migration in `alembic/versions/` |
| Change retry policy       | `app/core/config/settings.py` (`webhook_retry_delays_seconds`, `webhook_max_attempts`) |
| Add a background job      | New function in `app/workers/tasks.py` + register in `app/workers/settings.py::WorkerSettings.functions` |
| Add a cron                | Extend `_build_cron_jobs()` in `app/workers/settings.py`  |
| Add a frontend page       | `frontend/app/(protected)/<area>/page.tsx` + feature module under `frontend/features/<area>/` |
| Add a shadcn primitive    | `cd frontend && npx shadcn@latest add <name>`             |

## Tests

`tests/` is an async pytest suite driven by `pytest-asyncio` and
`pytest.ini`'s `asyncio_mode = auto`.

- The default test database is `postgresql+asyncpg://mailpulse:mailpulse@localhost:5433/mailpulse_test`.
  Override with `TEST_DATABASE_URL=… pytest`.
- `tests/conftest.py` creates and drops the schema per session via
  `Base.metadata.create_all` / `drop_all`, so migrations are not
  exercised by tests.
- Coverage tooling is **not configured**. Add `pytest-cov` if you want it.

## Debugging

- **API request trace**: every API request is logged by
  `app/core/middleware/request_logging.py` with method, path, status, and
  duration.
- **Worker job logs**: Arq logs every job enqueue and result. Pair the
  job ID with the corresponding Postgres row for correlation.
- **Database queries**: temporarily set `echo=True` on the engine in
  `app/database/session.py` to print SQL to stdout. Do not commit that
  change.
- **Redis queue length**:

  ```bash
  docker compose exec redis redis-cli LLEN arq:queue
  ```

## IDE setup

- **VS Code**: the repo is a Python + Next.js monorepo. Recommended
  extensions: Python, Pylance, ESLint, Tailwind CSS IntelliSense, Docker.
- **PyCharm**: mark `app/`, `tests/`, `alembic/` as Sources roots;
  configure the project interpreter to the uv-managed `.venv`.

## Pull request checklist

- [ ] `pytest` passes locally.
- [ ] New backend code has at least one test in `tests/`.
- [ ] New env vars are documented in the root `README.md` env table
      and in `docs/api.md` (if they affect the API contract).
- [ ] Frontend changes pass `npm run lint`.
- [ ] Migrations are checked in alongside model changes; do not edit
      existing migrations after they are merged.
- [ ] No secrets, real IMAP credentials, or production URLs in the diff.
