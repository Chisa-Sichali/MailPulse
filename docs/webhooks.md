# Webhooks

MailPulse delivers `email.received` events to your HTTPS endpoints with HMAC-SHA256 signatures.

## Register an endpoint

```http
POST /api/v1/webhooks
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://your-app.com/webhooks/email",
  "name": "Production"
}
```

Response includes `secret` (shown once). Store it securely.

## Payload format

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "email.received",
  "created_at": "2026-06-21T12:00:00+00:00",
  "data": {
    "message_id": "<msg@example.com>",
    "mailbox_id": "...",
    "from": { "email": "sender@example.com", "name": "Sender" },
    "to": ["you@example.com"],
    "subject": "Hello",
    "text_body": "...",
    "html_body": "...",
    "attachments": [{ "filename": "file.pdf", "content_type": "application/pdf", "size": 1234 }],
    "in_reply_to": null,
    "received_at": "2026-06-21T11:59:00+00:00"
  }
}
```

## Signature verification

Header:

```
MailPulse-Signature: t=1710000000,v1=<hex_hmac_sha256>
```

Algorithm:

1. Serialize payload to JSON (compact, sorted keys — same as sent)
2. Build string: `{timestamp}.{json_body}`
3. Compute `HMAC-SHA256(secret, signed_string)`
4. Compare hex digest to `v1` value using timing-safe comparison

Additional headers:

- `MailPulse-Event-Id` — event UUID
- `MailPulse-Webhook-Id` — webhook UUID

## Retries

Failed deliveries retry with delays: **1m → 5m → 30m → 2h** (configurable). After max attempts, status becomes `dead_lettered`.

View delivery logs: `GET /api/v1/webhooks/{id}/deliveries`

## Python verification example

```python
import hashlib
import hmac
import json

def verify(secret: str, body: bytes, header: str) -> bool:
    parts = dict(p.split("=", 1) for p in header.split(","))
    timestamp, signature = parts["t"], parts["v1"]
    signed = f"{timestamp}.{body.decode()}".encode()
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```
