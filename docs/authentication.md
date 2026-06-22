# Authentication

MailPulse uses JSON Web Tokens (JWT) for authentication.

## API Authentication Flow

1. **Login:** Clients send a POST request to `/api/v1/auth/login` with their credentials (`username` and `password` in `OAuth2PasswordRequestForm` format).
2. **Token Issuance:** The server validates the credentials and returns an `access_token` and a `refresh_token`.
3. **Accessing Protected Routes:** Clients include the access token in the `Authorization` header of subsequent requests:
   ```
   Authorization: Bearer <access_token>
   ```
4. **Token Expiration:** Access tokens expire relatively quickly (e.g., 30 minutes). When an access token expires, the client must use the `refresh_token` to obtain a new access token via the `/api/v1/auth/refresh` endpoint.

## API Keys
For programmatic access (e.g., integrating your own backend scripts), you can generate API keys. These keys do not expire by default and are passed in the same `Authorization` header format.

## Security Considerations
- Passwords are hashed using bcrypt before being stored in the database.
- IMAP credentials (passwords) are symmetrically encrypted at rest using Fernet and the `CREDENTIAL_ENCRYPTION_KEY`.
- Webhook secrets are also encrypted at rest.
