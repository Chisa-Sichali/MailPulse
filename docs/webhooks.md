# Webhooks

MailPulse delivers every parsed email to your application as a signed JSON
webhook. This page describes the payload, the headers, and how to verify
the signature.

## Lifecycle

1. You register a webhook via `POST /api/v1/webhooks` (see
   [api.md](api.md#create-webhook)). The response includes a `secret`
   starting with `whsec_` — **store it securely**. It is shown only once.
2. Whenever the worker saves a new `EmailEvent`, it enqueues a delivery for
   each of your webhooks subscribed to `email.received`.
3. Each delivery is signed and POSTed. On a 2xx response the delivery is
   marked `delivered`. On non-2xx (or a network/timeout error) the worker
   schedules a retry per `WEBHOOK_RETRY_DELAYS_SECONDS`.
4. After `WEBHOOK_MAX_ATTEMPTS` failed attempts the delivery is marked
   `dead_lettered`. Re-queue it any time via
   `POST /api/v1/events/{id}/retry`.

## Headers

Every POST contains:

| Header                    | Example                                | Purpose                                  |
| ------------------------- | -------------------------------------- | ---------------------------------------- |
| `Content-Type`            | `application/json`                     | Standard.                                |
| `User-Agent`              | `MailPulse-Webhook/1.0`                | Identifies the source.                   |
| `MailPulse-Signature`     | `t=1710000000,v1=<hex_hmac_sha256>`    | Timestamp + HMAC-SHA256 over the body.   |
| `MailPulse-Event-Id`      | event UUID                             | The `EmailEvent.id`.                     |
| `MailPulse-Webhook-Id`    | webhook UUID                           | The `Webhook.id`.                        |
| `MailPulse-Attempt`       | `1`                                    | 1-based attempt number for this delivery.|

## Payload

The body is a compact JSON document (no whitespace) with sorted keys, exactly
as signed:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "email.received",
  "created_at": "2026-06-21T12:00:00+00:00",
  "data": {
    "message_id": "<msg@example.com>",
    "mailbox_id": "…",
    "from": { "email": "sender@example.com", "name": "Sender" },
    "to": ["you@example.com"],
    "subject": "Hello",
    "text_body": "…",
    "html_body": "<p>…</p>",
    "attachments": [
      { "filename": "file.pdf", "content_type": "application/pdf", "size": 1234 }
    ],
    "in_reply_to": null,
    "received_at": "2026-06-21T11:59:00+00:00"
  }
}
```

Field reference:

- `id` — UUID of this delivery (mirrors the underlying `EmailEvent.id`).
- `type` — always `email.received` today. The list is extensible via
  `Webhook.event_types`.
- `created_at` — server time when the payload was signed.
- `data.message_id` — RFC822 `Message-ID` of the email.
- `data.mailbox_id` — UUID of the mailbox that received the email.
- `data.from` — sender as `{email, name}`.
- `data.to` — array of recipient strings.
- `data.subject`, `data.text_body`, `data.html_body` — parsed bodies.
- `data.attachments` — metadata only; the raw bytes are **not** delivered
  via webhook today.
- `data.in_reply_to` — RFC822 `In-Reply-To` if present (string).
- `data.received_at` — `Date` header parsed to UTC ISO-8601.

> The signing code uses `json.dumps(payload, separators=(",", ":"), sort_keys=True)`,
> so the bytes you receive are deterministic. **Do not re-serialise the
> payload before verifying the signature** — key order and whitespace
> differences will invalidate the HMAC.

## Signature verification

The header format is:

```
MailPulse-Signature: t=<unix_seconds>,v1=<hex_hmac_sha256>
```

Algorithm:

1. Parse `t` and `v1` from the header.
2. Build the signed string: `f"{t}.{raw_body}"` where `raw_body` is the
   exact bytes of the request body.
3. Compute `HMAC_SHA256(secret.encode(), signed_string.encode()).hexdigest()`.
4. Compare to `v1` with `hmac.compare_digest` (constant time).
5. Reject if `|now - t| > 300 seconds` (replay window, configurable per
   deployment by editing `tolerance_seconds` in `verify_webhook_signature`).

`app/core/security/webhook_signature.py` implements both signing and
verification; the verification function is what you should mirror.

### Python

```python
import hmac
import hashlib
import time


def verify(
    secret: str,
    body: bytes,
    signature_header: str,
    tolerance_seconds: int = 300,
) -> bool:
    parts = dict(item.split("=", 1) for item in signature_header.split(","))
    timestamp = int(parts["t"])
    signature = parts["v1"]

    if abs(int(time.time()) - timestamp) > tolerance_seconds:
        return False  # replay protection

    signed = f"{timestamp}.{body.decode()}".encode()
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### Node.js

```javascript
const crypto = require("node:crypto");

function verify(secret, rawBody, signatureHeader, toleranceSeconds = 300) {
  const parts = Object.fromEntries(
    signatureHeader.split(",").map((kv) => kv.split("=", 2))
  );
  const ts = parseInt(parts.t, 10);
  if (Math.abs(Math.floor(Date.now() / 1000) - ts) > toleranceSeconds) {
    return false; // replay protection
  }
  const signed = Buffer.from(`${ts}.${rawBody.toString()}`);
  const expected = crypto
    .createHmac("sha256", secret)
    .update(signed)
    .digest("hex");
  return crypto.timingSafeEqual(
    Buffer.from(expected),
    Buffer.from(parts.v1)
  );
}
```

### Go

```go
package main

import (
    "crypto/hmac"
    "crypto/sha256"
    "encoding/hex"
    "strconv"
    "strings"
    "time"
)

func Verify(secret string, body []byte, header string, tolerance int) bool {
    parts := map[string]string{}
    for _, kv := range strings.Split(header, ",") {
        k, v, _ := strings.Cut(kv, "=")
        parts[k] = v
    }
    ts, _ := strconv.ParseInt(parts["t"], 10, 64)
    if abs(time.Now().Unix()-ts) > int64(tolerance) {
        return false
    }
    mac := hmac.New(sha256.New, []byte(secret))
    mac.Write([]byte(strconv.FormatInt(ts, 10) + "." + string(body)))
    return hmac.Equal([]byte(hex.EncodeToString(mac.Sum(nil))), []byte(parts["v1"]))
}

func abs(x int64) int64 { if x < 0 { return -x }; return x }
```

## Retry semantics

- Backoff schedule: `WEBHOOK_RETRY_DELAYS_SECONDS` (default `[60, 300, 1800, 7200]`).
- A delivery is retried iff its current attempt is `< WEBHOOK_MAX_ATTEMPTS`
  and its last response was non-2xx (or it errored out).
- The `retry_failed_webhook_deliveries` cron job runs every minute and
  re-enqueues deliveries whose `next_retry_at` is in the past.
- After the final attempt, the delivery is marked `dead_lettered`. It is
  never auto-retried.
- Manual retry: `POST /api/v1/events/{id}/retry` re-enqueues fan-out for
  the underlying event, which produces fresh `webhook_deliveries` rows.

## Common pitfalls

- **Re-serialising the body** before verifying the signature. The HMAC is
  over the exact bytes MailPulse sent.
- **Treating timestamps as Unix milliseconds**. The header uses Unix
  seconds.
- **Allowing huge bodies**. MailPulse does not embed raw attachments, but
  HTML bodies can still be large. Consider a body-size cap in your
  receiver.
- **Returning 2xx for failures**. A handler that intends to retry a
  partial failure must return a non-2xx status.
- **Slow responses**. Long handlers eat into Arq's job timeout
  (`ARQ_JOB_TIMEOUT`, default 300 seconds). Respond first, process
  asynchronously.
