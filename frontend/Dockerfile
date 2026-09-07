# syntax=docker/dockerfile:1.7
# ─────────────────────────────────────────────────────────────────────────────
# MailPulse dashboard — Next.js 16 production image
#
# Three-stage build:
#   1. deps     — installs production + dev dependencies (devDeps needed at build)
#   2. builder  — runs `next build` with `output: "standalone"` so we can copy
#                 a minimal runtime tree into the final image
#   3. runner   — non-root Node Alpine image that runs `server.js` from .next/standalone
#
# Build context is expected to be the `frontend/` directory.
# ─────────────────────────────────────────────────────────────────────────────

# 1. Deps ──────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS deps
LABEL authors="chisa"

WORKDIR /app

# libc6-compat is required by Next.js / sharp on Alpine for DNS resolution
RUN apk add --no-cache libc6-compat

COPY package.json package-lock.json* ./
# `npm ci` is reproducible and faster than `npm install`; falls back gracefully
# if package-lock.json is missing via the wildcard above.
RUN npm ci --no-audit --no-fund

# 2. Builder ───────────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder
LABEL authors="chisa"

WORKDIR /app

RUN apk add --no-cache libc6-compat

# Reuse the installed node_modules from the deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build-time public env vars. Override at build-time with --build-arg if needed.
# These get inlined into the client bundle by Next.js, so changing them
# requires a rebuild.
ARG NEXT_PUBLIC_API_URL=http://localhost:3000
ARG NEXT_PUBLIC_FASTAPI_BACKEND_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} \
    NEXT_PUBLIC_FASTAPI_BACKEND_URL=${NEXT_PUBLIC_FASTAPI_BACKEND_URL} \
    NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production

RUN npm run build

# 3. Runner ────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS runner
LABEL authors="chisa"

WORKDIR /app

RUN apk add --no-cache libc6-compat curl \
    && addgroup --system --gid 1001 nodejs \
    && adduser  --system --uid 1001 nextjs

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# Copy the standalone server tree — this includes a minimal node_modules and
# server.js ready to run.
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
# Static assets and public/ still need to be served alongside the server.
COPY --from=builder --chown=nextjs:nodejs /app/.next/static        ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public               ./public

USER nextjs

EXPOSE 3000

# Lightweight healthcheck — Next.js responds 200 on the home page once it boots.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:3000/ || exit 1

CMD ["node", "server.js"]