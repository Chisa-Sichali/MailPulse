# syntax=docker/dockerfile:1.7
# ─────────────────────────────────────────────────────────────────────────────
# MailPulse API — uv-managed production image
#
# Build strategy (per official uv Docker guide):
#   1. builder — `uv sync --locked` installs the exact dependency set from
#                uv.lock into a dedicated .venv. `--no-install-project` skips
#                installing the app itself (source is copied at runtime).
#   2. runner  — slim python:3.11-slim image that only carries the venv +
#                app source + alembic migrations. No pip, no uv, no build
#                toolchain → smaller image, smaller attack surface.
#
# Version bumps must go through pyproject.toml + `uv lock`, never by editing
# this file.
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim AS builder

WORKDIR /app

# Pin uv for reproducibility (checksum-verified, fetched from astral-sh).
COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /uvx /bin/

# Manifest files first so dependency layers cache independently of source.
COPY pyproject.toml uv.lock ./

# Install the locked dependency set. --no-cache keeps the layer lean;
# --no-install-project keeps `mailpulse` itself out of site-packages.
RUN uv sync --locked --no-dev --no-install-project --no-cache

# ── Runtime ──────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Venv first (largest, most stable layer), then the app source.
COPY --from=builder /app/.venv /app/.venv
COPY . .

# Alembic needs its config + migrations present at image runtime.
EXPOSE 8080

# Liveness probe — GET / returns {"status": "healthy"} without touching the DB.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8080/ || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]