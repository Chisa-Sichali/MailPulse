# API Reference

The MailPulse API is built with FastAPI and follows RESTful conventions.

## Base URL
`/api/v1`

## OpenAPI Documentation
FastAPI automatically generates interactive API documentation. When the server is running, you can access it at:
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

## Key Endpoints

### Authentication
- `POST /auth/login`: Authenticate and receive access/refresh tokens.
- `POST /auth/refresh`: Obtain a new access token using a refresh token.
- `POST /auth/register`: Create a new user account.

### Mailboxes
- `GET /mailboxes`: List all configured mailboxes.
- `POST /mailboxes`: Add a new IMAP mailbox to monitor.
- `GET /mailboxes/{id}`: Get details for a specific mailbox.
- `PATCH /mailboxes/{id}`: Update mailbox settings.
- `DELETE /mailboxes/{id}`: Remove a mailbox.

### Webhooks
- `GET /webhooks`: List all configured webhooks.
- `POST /webhooks`: Create a new webhook destination.
- `PATCH /webhooks/{id}`: Update webhook settings.
- `POST /webhooks/{id}/test`: Trigger a test payload to the webhook.
- `GET /webhooks/{id}/deliveries`: View the delivery history for a specific webhook.

### Events
- `GET /events`: List parsed email events.
- `POST /events/{id}/retry`: Manually retry dispatching an event.
