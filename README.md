---
title: Lead Processing System
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# Lead Processing System

Monorepo with two FastAPI microservices:

- `landings`: accepts leads, validates JWT, validates affiliate/offer, pushes leads to Redis queue.
- `core`: starts background worker, reads queue via `BLPOP`, deduplicates with Redis TTL (10 min), stores new leads in PostgreSQL, exposes analytics API.

## Project structure

- `common/` shared DB models, security, schemas.
- `landings/` lead intake service.
- `core/` analytics + worker service.
- `Dockerfile.landings` and `Dockerfile.core` for separate deploys.

## Environment variables

Create local env file from template:

```bash
copy .env.example .env
```

Then fill values in `.env`:

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:6543/DB_NAME
REDIS_URL=redis://default:password@host:6379
JWT_SECRET=change-me
JWT_ALGORITHM=HS256
LEADS_QUEUE_NAME=leads_queue
```

## Install and run locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Run `landings`:

```bash
uvicorn landings.main:app --reload --port 8001
```

Run `core`:

```bash
uvicorn core.main:app --reload --port 8002
```

## API

- `POST /lead` on `landings`
  - Header: `Authorization: Bearer <jwt>`
  - Body: `affiliate_id`, `offer_id`, `name`, `phone`
- `GET /leads` on `core`
  - Header: `Authorization: Bearer <jwt>`
  - Returns aggregated leads by `affiliate_id` + `offer_id`

## Notes

- Before production usage, add Alembic migration files and initialize DB schema (`affiliates`, `offers`, `leads`).
- JWT validation currently checks `affiliate_id` claim and verifies such affiliate exists in DB.
