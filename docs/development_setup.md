# Development Setup

This guide will help you set up MailPulse for local development.

## Prerequisites
- Python 3.11+
- Node.js 20+
- Docker and Docker Compose

## Backend Setup
1. Clone the repository.
2. Set up a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in any necessary values.
5. Start the required infrastructure (PostgreSQL and Redis) using Docker:
   ```bash
   docker compose up -d postgres redis
   ```
6. Run database migrations:
   ```bash
   alembic upgrade head
   ```
7. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8080
   ```
8. In a separate terminal, start the Arq worker:
   ```bash
   arq app.workers.settings.WorkerSettings
   ```

## Frontend (Dashboard) Setup
1. Navigate to the `dashboard` directory:
   ```bash
   cd dashboard
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
The dashboard will be available at `http://localhost:5173`.
