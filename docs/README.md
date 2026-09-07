# MailPulse Documentation

This directory contains the long-form documentation for MailPulse. The
top-level [`README.md`](../README.md) is the entry point — start there for a
project overview, architecture diagram, and quick start. The pages below
cover specific subsystems in depth.

## Contents

| Document                                       | Audience                | Purpose                                                                |
| ---------------------------------------------- | ----------------------- | ---------------------------------------------------------------------- |
| [architecture.md](architecture.md)             | everyone                | System design, component responsibilities, request sequence diagrams. |
| [api.md](api.md)                               | API consumers           | REST endpoint catalogue with request/response shapes.                  |
| [authentication.md](authentication.md)         | API consumers, contributors | JWT and refresh token mechanics, hashing, encryption.              |
| [database.md](database.md)                     | contributors            | Schema, models, indexes, migrations.                                   |
| [webhooks.md](webhooks.md)                     | API consumers           | Webhook payload format, headers, signature verification.               |
| [workers.md](workers.md)                       | contributors, operators | Arq job catalogue, cron schedule, retry semantics.                     |
| [email-processing.md](email-processing.md)     | contributors            | How an email moves from IMAP to a saved `EmailEvent`.                  |
| [dashboard.md](dashboard.md)                   | dashboard contributors  | Next.js dashboard setup, structure, configuration.                     |
| [development.md](development.md)               | contributors            | Local dev workflow, scripts, debugging.                                |
| [deployment.md](deployment.md)                 | operators               | Production deployment, secrets, reverse proxy.                         |
| [troubleshooting.md](troubleshooting.md)       | everyone                | Common problems and fixes.                                             |

## When to read which

- I want to **understand the system** → [architecture.md](architecture.md)
- I want to **integrate with the API** → [api.md](api.md) + [webhooks.md](webhooks.md) + [authentication.md](authentication.md)
- I want to **set up a dev environment** → [development.md](development.md)
- I want to **run the dashboard** → [dashboard.md](dashboard.md)
- I want to **deploy it** → [deployment.md](deployment.md)
- I want to **fix something that is broken** → [troubleshooting.md](troubleshooting.md)
- I want to **modify the schema** → [database.md](database.md)
- I want to **modify the worker / retry policy** → [workers.md](workers.md)
- I want to **change email parsing** → [email-processing.md](email-processing.md)

## Conventions

Throughout the docs:

- `app/` paths are relative to the repository root.
- `frontend/` paths are inside the Next.js project.
- Code blocks use `bash` for shell commands, `python`/`typescript` for source,
  `json` for payloads, and `text` for directory trees.
- Mermaid diagrams render natively on GitHub.

## Updating documentation

The docs are kept in lockstep with the code. When you change behaviour, update
the relevant page (or add a new one) in the same pull request.
