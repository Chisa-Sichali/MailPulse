# Dashboard

The MailPulse dashboard is a React application in the `dashboard/` folder. It uses **Urbanist** at a compact **13px** base size for a professional, data-dense SaaS feel.

## Setup

```powershell
cd dashboard
copy .env.example .env
npm install
npm run dev
```

Default URL: http://localhost:5173

## Configuration

`dashboard/.env`:

```env
VITE_API_URL=http://localhost:8080
```

The API must allow CORS from the dashboard origin (configured by default in backend `CORS_ORIGINS`).

## Pages

| Route | Description |
|-------|-------------|
| `/login` | Sign in or register |
| `/` | Overview — KPIs, volume chart, resources |
| `/mailboxes` | Add and manage IMAP mailboxes |
| `/webhooks` | Register endpoints, test delivery |
| `/events` | Recent email events |
| `/analytics` | Top senders, webhook performance |
| `/health` | Database, Redis, queue status |

## Design

- **Font:** Urbanist (Google Fonts)
- **Base size:** 13px (`html { font-size: 13px }`)
- **Labels:** 10px uppercase (`text-2xs`)
- **Layout:** Dark sidebar, light content area

## Production build

```powershell
npm run build
npm run preview
```

Serve the `dashboard/dist` folder with any static host, or add a reverse proxy to your API domain.

## Authentication

Tokens are stored in `localStorage`. The dashboard automatically refreshes expired access tokens using the refresh token.
