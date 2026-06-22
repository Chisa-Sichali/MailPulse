# Deployment

MailPulse is designed to be deployed using Docker and Docker Compose.

## Prerequisites
- Docker Engine
- Docker Compose
- A domain name (optional, for exposing the dashboard and API via a reverse proxy)

## Services
The `docker-compose.yml` file defines the following services:
1. **`postgres`**: The PostgreSQL 16 database.
2. **`redis`**: The Redis 7 instance for job queuing.
3. **`api`**: The FastAPI application serving the API.
4. **`worker`**: The Arq worker process handling background tasks.
5. **`dashboard`**: The React/Vite frontend served via Nginx.

## Environment Variables
Before deploying, ensure you have a properly configured `.env` file based on `.env.example`. Make sure to set strong, random values for:
- `JWT_SECRET_KEY`
- `CREDENTIAL_ENCRYPTION_KEY`

## Deployment Steps
1. Clone the repository to your server.
2. Create and populate the `.env` file.
3. Run `docker compose up -d` to start all services in detached mode.
4. The database migrations will automatically run when the `api` and `worker` containers start.

## Reverse Proxy
In a production environment, you should not expose the API (port 8080) and Dashboard (port 3000) directly to the internet. Instead, use a reverse proxy like Nginx, Traefik, or Caddy to handle SSL termination and route traffic to the appropriate containers.
