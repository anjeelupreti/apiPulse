# backend — my notes

This is the Django + DRF API. If I've been away from this for a while, here's what I need to remember to get it running again, plus why I set some things up the way I did.

## Getting it running from scratch

```bash
cd backend
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # Mac/Linux

cp .env.example .env      # then fill in real values if this isn't just local dev

cd ../deployment
docker compose up -d      # Postgres + Redis

cd ../backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

That gets me the API + admin. If I also want the monitoring engine actually running (pinging URLs on schedule), I need two more processes, each in their own terminal, venv activated:

```bash
# terminal 2 — the worker that actually does the pinging
python -m celery -A config worker --pool=solo -l info
# --pool=solo because I'm on Windows — Celery's default worker pool
# (prefork) just doesn't work there. On Mac/Linux I could drop this flag.

# terminal 3 — the clock that tells the worker when to ping something
python -m celery -A config beat -l info
```

If I only run the worker and not beat, nothing happens automatically — beat is the thing that actually decides "it's been N seconds, go check this monitor." Without it the queue just sits empty forever.

## Why I laid out settings/ as a package instead of one settings.py

`config/settings/base.py` has everything shared. `dev.py` and `prod.py` each do `from .base import *` and then override just the handful of things that actually differ (DEBUG, ALLOWED_HOSTS, CORS, SSL redirect stuff). Which one loads is controlled by `DJANGO_ENV` in `.env` — unset or anything other than `prod` gets you `dev.py`.

I did it this way instead of a single settings.py with a bunch of `if DEBUG:` branches because I kept almost shipping dev settings to prod by accident when it was all one file. Splitting them makes it obvious which file you're editing.

## Why apps/ isn't just Django's default layout

`django-admin startproject` puts your apps next to `manage.py`, flat. I moved mine into `apps/monitors`, `apps/checks`, etc., and then in `settings/base.py` I do:

```python
sys.path.append(str(BASE_DIR / 'apps'))
```

so I can still write `'monitors'` in `INSTALLED_APPS` instead of `'apps.monitors'`. Purely cosmetic reason, honestly — I just wanted `backend/` to visually separate "the apps" from "the project config" (`config/`) instead of having 7 folders sitting side by side at the same level.

## The apps, and why each one exists

I split by concern instead of one big app, because when something's broken I want to know which file to open without guessing:

- **[accounts](apps/accounts/README.md)** — who's logged in
- **[monitors](apps/monitors/README.md)** — what I'm watching, and the scheduler that decides what's due
- **[checks](apps/checks/README.md)** — the actual ping logic + one row per result
- **[incidents](apps/incidents/README.md)** — deciding when a string of failures becomes an "outage"
- **[alerts](apps/alerts/README.md)** — notifications, not built yet

Each has its own README — go there for model fields, the actual API routes, and the reasoning behind that app specifically.

## The API surface (top level)

| Path | What's there |
|---|---|
| `/admin/` | Django admin — quick way to poke at the DB without curl |
| `/api/auth/` | DRF's login/logout views (mainly so the browsable API works) |
| `/api/monitors/` | full CRUD, see monitors README |
| `/api/checks/` | read-only, see checks README |
| `/api/incidents/` | read-only, see incidents README |

Auth right now is Django session auth (cookie, if I'm logged into `/admin/`) or HTTP Basic auth (for curl / testing). Neither of these is what I want once there's a real frontend — I'll need token or JWT auth for that, haven't built it yet.

Every viewset scopes its queryset to `request.user` — `Monitor.objects.filter(owner=request.user)`, and Checks/Incidents filter through `monitor__owner=request.user`. So logging in as a different user shows a completely different (empty, until they add monitors) list. That's the "each user has their own space" behavior, currently at the individual-user level — no shared team workspaces yet.

## Quick sanity check that it's all wired up

```bash
curl -u admin:yourpassword http://127.0.0.1:8000/api/monitors/
```

Should come back with a paginated JSON list (empty array is fine, that just means no monitors yet). A 403 means auth isn't going through — check I'm passing `-u user:pass` and the user actually exists (`python manage.py createsuperuser`).
