# Database Schema

MailPulse uses PostgreSQL to store its state. SQLAlchemy is used as the ORM.

## Core Models

### `User`
Represents an authenticated user in the system.
- **Fields:** `id`, `email`, `hashed_password`, `is_active`, `is_superuser`, `created_at`, `updated_at`.
- **Relationships:** Has many `Mailboxes`, `Webhooks`, `ApiKeys`.

### `Mailbox`
Stores the IMAP credentials and connection settings for a mailbox to be monitored.
- **Fields:** `id`, `user_id`, `email_address`, `imap_host`, `imap_port`, `imap_username`, `encrypted_password`, `is_enabled`, `last_synced_at`, `health_status`, `error_message`.
- **Relationships:** Belongs to a `User`. Has many `EmailEvents`.
- **Security:** The IMAP password is encrypted at rest.

### `EmailEvent`
Stores the parsed content of a received email.
- **Fields:** `id`, `mailbox_id`, `message_id`, `imap_uid`, `sender_email`, `sender_name`, `recipients`, `subject`, `text_body`, `html_body`, `attachments_metadata`, `in_reply_to`, `received_at`, `status`.
- **Relationships:** Belongs to a `Mailbox`. Has many `WebhookDeliveries`.

### `Webhook`
Defines a destination URL for email events.
- **Fields:** `id`, `user_id`, `name`, `url`, `encrypted_secret`, `secret_prefix`, `event_types`, `is_enabled`.
- **Relationships:** Belongs to a `User`. Has many `WebhookDeliveries`.

### `WebhookDelivery`
Tracks the attempt to send an `EmailEvent` to a specific `Webhook`.
- **Fields:** `id`, `webhook_id`, `email_event_id`, `status` (pending, delivered, failed), `attempt_count`, `next_retry_at`, `http_status_code`, `response_body`, `error_message`.
- **Relationships:** Belongs to a `Webhook` and an `EmailEvent`.

### `ApiKey`
Allows programmatic access to the MailPulse API.
- **Fields:** `id`, `user_id`, `name`, `key_prefix`, `hashed_key`, `expires_at`, `last_used_at`, `is_active`.
- **Relationships:** Belongs to a `User`.
