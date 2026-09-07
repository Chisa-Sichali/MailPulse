# Deployment

This page covers taking MailPulse from a working local stack to a hosted
environment.

The repository does **not** ship managed-platform manifests (AWS App Runner,
Fly, Render, Cloud Run, etc.). The supported deployment unit is
`docker-compose.yml`, optionally fronted by a reverse proxy.

## Deployment topologies

### 1. Single-node Docker Compose (default)

The `docker-compose.yml` in the repo root provisions five services on a
shared network:

| Service     | Image / build         | Port (host) | Internal port |
| ----------- | --------------------- | ----------- | ------------- |
| `postgres`  | `postgres:16-alpine`  | `5433`      | `5432`        |
| `redis`     | `redis:7-alpine`      | `6379`      | `6379`        |
| `api`       | built from `Dockerfile` | `8080`    | `8080`        |
| `worker`    | built from `Dockerfile` | —         | —             |
| `dashboard` | built from `frontend/Dockerfile` | `3000` | `3000` |
| `env-gen`   | `alpine:3.20` (one-shot) | —       | —             |

This is appropriate for:

- Self-hosted single-node deployments
- Staging environments
- Evaluation / demo setups

### 2. Compose + external Postgres / Redis

Recommended for anything you intend to keep online. Replace the bundled
`postgres` and `redis` services with managed instances and point the API
and worker at them via `DATABASE_URL` and `REDIS_URL`.

```yaml
# In an override file (e.g. docker-compose.prod.yml)
services:
  api:
    environment:
      DATABASE_URL: postgresql+asyncpg://user:pass@db.internal:5432/mailpulse
      REDIS_URL: redis://redis.internal:6379/0
    depends_on: []  # external services
  worker:
    environment:
      DATABASE_URL: postgresql+asyncpg://user:pass@db.internal:5432/mailpulse
      REDIS_URL: redis://redis.internal:6379/0
    depends_on: []
```

Run with:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 3. Kubernetes / ECS / Nomad

The five services map cleanly to five workload types. Use the existing
Dockerfiles; do not write new ones. Each worker container should be
stateless and can be scaled horizontally against the same Redis instance.

## Required environment

Before any production deployment, replace the dev defaults in `.env`:

```bash
scripts/generate-env.sh        # populates with strong random secrets
```

Verify these are **not** the defaults:

| Variable                     | Why                                                            |
| ---------------------------- | -------------------------------------------------------------- |
| `JWT_SECRET_KEY`             | Signs every access token.                                      |
| `CREDENTIAL_ENCRYPTION_KEY`  | Encrypts every stored mailbox password and webhook secret. Losing this permanently destroys all encrypted rows. |
| `CRON_SECRET_KEY`            | Reserved for future cron-protected routes.                     |

`POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` only matter when
running the bundled Postgres container; ignore them when using an external
database.

## Build and start

```bash
# 1. Generate .env (idempotent)
scripts/generate-env.sh

# 2. Build images and start all services in the background
docker compose up -d --build

# 3. Confirm health
curl http://localhost:8080/health/system
```

Migrations run automatically via the `api` and `worker` `command:` —
both do `alembic upgrade head` before launching their main process.

## Reverse proxy

Do not expose ports `8080` and `3000` directly to the public internet on a
production deployment. Front the API and dashboard with a reverse proxy
that handles TLS termination.

Minimal Nginx configuration for a single host:

```nginx
server {
  listen 443 ssl http2;
  server_name api.example.com;

  ssl_certificate     /etc/letsencrypt/live/api.example.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

  location / {
    proxy_pass         http://127.0.0.1:8080;
    proxy_http_version 1.1;
    proxy_set_header   Host              $host;
    proxy_set_header   X-Real-IP         $remote_addr;
    proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header   X-Forwarded-Proto $scheme;
    proxy_read_timeout 300s;  # > ARQ_JOB_TIMEOUT
  }
}

server {
  listen 443 ssl http2;
  server_name app.example.com;

  ssl_certificate     /etc/letsencrypt/live/app.example.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/app.example.com/privkey.pem;

  location / {
    proxy_pass         http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header   Host              $host;
    proxy_set_header   X-Real-IP         $remote_addr;
    proxy_set_header   X-Forwarded-Proto $scheme;
  }
}
```

When you put the dashboard behind a different origin than the API, update
`CORS_ORIGINS` to include that origin.

## Persistent state

- **Postgres data**: backed by the `postgres_data` named volume in
  `docker-compose.yml`. Back this up with `pg_dump` on a schedule.
- **Logs**: container stdout is captured by Docker's log driver. Configure
  your driver to ship logs to your aggregator of choice.
- **Redis**: ephemeral. Arq recreates job state from Postgres on restart;
  in-flight jobs at the moment of a Redis loss are not replayed.

## Scaling

| Concern               | Direction                                                          |
| --------------------- | ------------------------------------------------------------------ |
| More API throughput   | Run multiple `api` containers behind a load balancer (stateless).  |
| More worker throughput | Run multiple `worker` containers against the same Redis. Each is independent. |
| More webhook destinations | Vertical — raise `ARQ_JOB_TIMEOUT` and lower `WEBHOOK_RETRY_DELAYS_SECONDS` if needed. |
| Database size         | Standard Postgres scaling (vertical first; partitioning on `email_events.created_at` if you keep very long histories). |

## Backup and restore

```bash
# Backup
docker compose exec postgres pg_dump -U mailpulse mailpulse \
  > backup-$(date -u +%Y%m%dT%H%M%SZ).sql

# Restore
cat backup-….sql | docker compose exec -T postgres psql -U mailpulse -d mailpulse
```

Restore is destructive; it drops and recreates rows in dependency order.

## Observability

- **Logs**: Rich-formatted to stdout. Pipe to your aggregator with a
  Docker logging driver.
- **Health checks**: `GET /health/system` probes Postgres and Redis and
  reports delivery counts. Wire this into your uptime monitor.
- **Metrics**: Prometheus exporter is **not** included. Add
  `prometheus-fastapi-instrumentator` if you need it.
- **Tracing**: OpenTelemetry is **not** wired up. Drop in
  `opentelemetry-instrumentation-fastapi` if you need distributed traces.

## What is NOT in the deployment story

- Managed-platform manifests (AWS App Runner, Fly, Render, etc.).
- TLS certificates (use your reverse proxy or a sidecar like `caddy`).
- Automated CI/CD pipelines — see [development.md](development.md) for the
  local workflow.
- A migration safety net beyond what Alembic already provides.

If you need any of these, treat them as project work: spin up an issue
and submit a PR.
