# deployment — my notes

Right now this folder is just a `docker-compose.yml` for local dev. It's not an actual production deployment setup yet — no Dockerfiles for the backend/frontend, no nginx, no CI. Just "give me Postgres and Redis without installing them on my machine directly."

## What's in here right now

```bash
cd deployment
docker compose up -d     # starts both, in the background
docker compose ps        # check they're actually running
docker compose down      # stop them (data survives, it's in named volumes)
docker compose down -v   # stop AND wipe the data — only if I actually want a clean slate
```

Two services:

- **postgres** (port 5432) — the main database. Same one Django connects to via `DATABASES` in `backend/config/settings/base.py`. Credentials here (`pulsewatch`/`pulsewatch`) match the defaults in `backend/.env.example` — if I change one, I have to change the other.
- **redis** (port 6379) — Celery's broker + result backend. Not a database in the "stores my data long-term" sense — if I `docker compose down -v` this one, I just lose queued/pending task state, not anything I actually care about keeping.

Why Docker instead of installing Postgres/Redis natively on Windows: mainly so I'm not fighting Windows-specific install quirks, and so wiping/resetting either one is just `docker compose down -v` instead of an uninstall.

## Why there's no Dockerfile for the backend itself yet

The Django app currently runs directly on my machine via the venv (`backend/.venv`), not inside a container — that's simpler while I'm actively developing (no rebuilding an image every time I change a line of Python). Once I actually care about deploying this somewhere real, I'll add:

- a `Dockerfile` for `backend/` (gunicorn + the Django app)
- a `Dockerfile` for `frontend/` (once it exists — probably a build step + nginx to serve the static files)
- `celery worker` and `celery beat` as their own services in this compose file, instead of me running them manually in terminals
- probably a separate `docker-compose.prod.yml` or an override file, since dev and prod needs diverge a lot (I don't want prod Postgres data in a throwaway local volume, for instance)

None of that exists yet — this file is intentionally just the two things I need to develop against locally.
