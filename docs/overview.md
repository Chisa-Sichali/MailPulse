# MailPulse Overview

MailPulse is a modern, reliable, and scalable email event processing platform. It acts as a bridge between IMAP mailboxes and webhook-capable applications, converting unstructured email data into structured, real-time JSON events.

## Why MailPulse?
Processing email reliably is notoriously difficult. Many applications need to react to incoming emails, but doing so directly involves:
- Maintaining persistent IMAP connections or constantly polling.
- Parsing complex MIME structures, encodings, and attachments.
- Handling transient network failures or downtime of the receiving service.

MailPulse solves these problems by providing a decoupled, event-driven architecture.

## Core Concepts

1. **Mailboxes:** IMAP accounts monitored by MailPulse.
2. **Email Events:** Parsed and structured representations of incoming emails.
3. **Webhooks:** User-defined HTTP endpoints that receive Email Events.
4. **Deliveries:** The actual HTTP POST attempts made by MailPulse to a Webhook.

## High-Level Data Flow

1. MailPulse polls configured IMAP mailboxes on a schedule.
2. New emails are fetched, parsed, and saved to the database.
3. An `email.received` event is generated.
4. The event is enqueued for fan-out to all active webhooks for that user.
5. Background workers attempt delivery, implementing retries and exponential backoff on failure.
