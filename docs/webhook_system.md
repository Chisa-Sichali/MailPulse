# Webhook System

MailPulse delivers email events to your applications via webhooks.

## Payload Structure
When an email is received, MailPulse sends a POST request to your configured webhook URL with a JSON payload:

```json
{
  "id": "event_uuid",
  "type": "email.received",
  "created_at": "2026-06-21T12:00:00Z",
  "data": {
    "message_id": "<test@example.com>",
    "mailbox_id": "mailbox_uuid",
    "from": {"email": "sender@example.com", "name": "Sender Name"},
    "to": ["receiver@example.com"],
    "subject": "Hello World",
    "text_body": "This is the plain text body.",
    "html_body": "<p>This is the HTML body.</p>",
    "attachments": [],
    "in_reply_to": null,
    "received_at": "2026-06-21T11:59:50Z"
  }
}
```

## Security & Signing
To verify that requests genuinely originate from MailPulse, every request includes a cryptographic signature in the headers.
When you create a webhook, MailPulse returns a one-time `secret`. 

**Headers Included:**
- `MailPulse-Signature`: Contains the timestamp and HMAC-SHA256 signature (e.g., `t=1718990000,v1=abc123def456...`).
- `MailPulse-Event-Id`: The UUID of the event.
- `MailPulse-Webhook-Id`: The UUID of the webhook.

**Verification Flow:**
1. Extract `t` and `v1` from the `MailPulse-Signature` header.
2. Reconstruct the payload: `signed_content = f"{t}.{request_body_string}"`.
3. Compute the HMAC-SHA256 digest using your `secret`.
4. Compare your digest with `v1`.

## Retry Logic & Failure Handling
If your server responds with a non-2xx status code, or the connection times out, MailPulse will retry the delivery.
- **Backoff Strategy:** Defined by `WEBHOOK_RETRY_DELAYS_SECONDS` (e.g., 1m, 5m, 30m, 2h).
- **Dead Letter Queue:** If the maximum attempts (`WEBHOOK_MAX_ATTEMPTS`) are reached, the delivery is marked as failed and requires manual intervention (or API retry) to re-process.
