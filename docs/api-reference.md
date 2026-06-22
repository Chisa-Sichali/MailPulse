# API Reference

Base URL: `http://localhost:8080`

All authenticated routes require header: `Authorization: Bearer <access_token>`

## Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Get tokens |
| POST | `/api/v1/auth/refresh` | Rotate access token |
| POST | `/api/v1/auth/logout` | Revoke refresh token |
| GET | `/api/v1/auth/me` | Current user |

## Mailboxes

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/mailboxes` | Add mailbox |
| GET | `/api/v1/mailboxes` | List |
| GET | `/api/v1/mailboxes/{id}` | Detail |
| PATCH | `/api/v1/mailboxes/{id}` | Update |
| DELETE | `/api/v1/mailboxes/{id}` | Soft delete |
| POST | `/api/v1/mailboxes/{id}/test-connection` | Test IMAP |

## Webhooks

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/webhooks` | Register (returns secret once) |
| GET | `/api/v1/webhooks` | List |
| PATCH | `/api/v1/webhooks/{id}` | Update |
| DELETE | `/api/v1/webhooks/{id}` | Delete |
| POST | `/api/v1/webhooks/{id}/rotate-secret` | New signing secret |
| POST | `/api/v1/webhooks/{id}/test` | Test delivery |
| GET | `/api/v1/webhooks/{id}/deliveries` | Delivery log |

## Events

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/events` | List (paginated) |
| GET | `/api/v1/events/{id}` | Detail |
| POST | `/api/v1/events/{id}/retry` | Re-queue |

## Analytics

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/analytics/overview?days=7` | KPIs |
| GET | `/api/v1/analytics/top-senders?days=7` | Top senders |
| GET | `/api/v1/analytics/volume?days=30` | Daily volume |
| GET | `/api/v1/analytics/webhooks?days=7` | Webhook performance |
| GET | `/api/v1/analytics/resources` | Mailbox/webhook counts |

## Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Liveness |
| GET | `/health/ready` | DB readiness |
| GET | `/health/system` | Full system status |

## Legacy

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/run-email-check` | Queue mailbox poll (cron Bearer token) |

Full interactive docs: http://localhost:8080/docs
