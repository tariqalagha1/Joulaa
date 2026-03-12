# Local Stability Runbook

## Purpose

This runbook captures the current local boot path for the repository without changing application logic. It is a stability reference for foundation work.

## Required Environment Variables

The repository already includes a root `.env.example`. Minimum keys currently referenced by backend/frontend startup paths:

- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `FRONTEND_URL`
- `BACKEND_URL`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`

Recommended local workflow:

```bash
cp .env.example .env
```

## Docker Compose Services

Current compose file defines these services:

- `postgres`
- `redis`
- `minio`
- `backend`
- `frontend`
- `celery-worker`
- `celery-beat`
- `mailhog`
- `adminer`

For baseline boot verification, only start database/cache first:

```bash
docker compose up -d postgres redis
```

## Backend Manual Run

Run from the `backend` directory:

```bash
uvicorn app.main:app --reload
```

If needed, explicitly bind the default port:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend Run

Run from the repository root:

```bash
npm run dev
```

Or directly from `frontend/`:

```bash
cd frontend
npm run dev
```

## Verification Targets

Backend health:

```bash
curl http://127.0.0.1:8000/health
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Frontend:

```text
http://127.0.0.1:3000
http://127.0.0.1:3000/login
```

## Database Reset

Current repository does not provide a stable, verified reset script. The simplest local reset path is destructive and should only be used in development:

```bash
docker compose down -v
docker compose up -d postgres redis
```

If PostgreSQL is running and you only want to recreate schema through init scripts, remove the Docker volume and restart the container stack.

## Known Startup Issues

- The repository contains duplicate backend database/auth paths:
  - `backend/app/core/database.py`
  - `backend/app/database.py`
  - `backend/app/core/security.py`
  - `backend/app/core/auth.py`
- Some endpoints import `get_db` from different modules, so runtime behavior is inconsistent.
- `docker-compose.yml` references build target `development`, but the current Dockerfiles should be treated as suspect until validated against actual build output.
- Worker services reference `app.core.celery`, which is not currently confirmed as present.
- Frontend startup depends on installed Node modules; backend startup depends on installed Python dependencies.
- Current auth tokens are stored in browser `localStorage`.

## Stability Notes

- Do not refactor during boot verification.
- Freeze observed behavior before changing auth, tenant enforcement, migrations, or workers.
- Use this runbook as the baseline record for all later foundation-hardening work.
