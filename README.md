# PulseWatch (apiPulse) — my notes

This is my API monitoring / uptime project. The idea: I register a URL, the system pings it on a schedule, logs what happened, and opens an incident if it starts failing repeatedly.

I'm writing this doc mostly for myself, so that when I come back to this in a few weeks I remember *why* things are structured this way, not just *what* the code does. Each folder has its own README going deeper into that piece — this one is just the map.

## How I'm thinking about the architecture

```
                    ┌──────────────┐
                    │   Browser    │   (frontend/ — haven't built this yet)
                    └──────┬───────┘
                           │ HTTP (REST API)
                           ▼
                    ┌──────────────┐
                    │ Django + DRF │   backend/  — my API server
                    │  (backend/)  │
                    └──────┬───────┘
                           │ reads/writes
                           ▼
                    ┌──────────────┐
                    │  PostgreSQL  │   Monitors, Checks, Incidents, Users
                    └──────────────┘
                           ▲
                           │ reads/writes
                    ┌──────┴───────┐        ┌──────────────┐
                    │Celery worker │◄───────│ Celery beat  │
                    │ (pings URLs) │  Redis  │ (the clock)  │
                    └──────┬───────┘  queue  └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ External API │   whatever URL I'm monitoring
                    │ / website    │
                    └──────────────┘
```

The thing I had to get straight in my head: there are **two completely separate things** touching the database, on two separate rhythms.

1. **Me, through the API.** I hit `POST /api/monitors/` to register a URL. Totally normal request/response, nothing special.
2. **The monitoring engine, running in the background, on its own clock.** Every 15 seconds, **Celery beat** wakes up and asks "which monitors are due for a check?" (beat itself does zero real work — it's just a scheduler). For each monitor that's due, it drops a job onto a **Redis** queue. A separate process, the **Celery worker**, is the one actually pulling jobs off that queue, pinging the real URL, and writing the result.

Why not just ping the URL directly inside the Django view when someone hits the API? Because pinging some random external URL can be slow or hang entirely (timeouts, DNS issues, whatever) — and I don't want *my* API to freeze up because *someone else's* server is slow. That's the whole reason the background worker exists — it absorbs that unpredictability so the API stays fast.

## Where I put things

```
apiPulse/
├── backend/        Django + DRF — see backend/README.md
│   └── apps/
│       ├── accounts/   who's logged in
│       ├── monitors/   what I'm watching (+ the scheduler task)
│       ├── checks/     the ping results (+ the actual ping task)
│       ├── incidents/  outage tracking (+ open/resolve logic)
│       └── alerts/     notifications — haven't built this yet
├── frontend/       React dashboard — haven't built this yet
└── deployment/     docker-compose for Postgres/Redis
```

I split these into separate Django apps on purpose, one concern each, instead of dumping everything into one giant app. The rule I'm following: `monitors` doesn't know *how* to ping a URL, it just holds the config and hands off to `checks`. `checks` doesn't decide what counts as an "outage," it just records what happened and hands off to `incidents`. That way when I'm confused about a bug, I only have to hold one app's logic in my head at a time.

## How I run this locally

1. **Spin up Postgres + Redis**: `cd deployment && docker compose up -d`
2. **API server**: set up the venv in `backend/` (see backend/README.md), then `python manage.py runserver`
3. **Monitoring engine** (only needed if I actually want checks to run): start a Celery worker + Celery beat, both documented in backend/README.md
4. **Frontend**: nothing here yet

## What's actually done vs. what I still owe myself

| Piece | Status |
|---|---|
| Custom User model, Postgres, env-based settings | done |
| Monitor CRUD API | done |
| Celery engine — pings monitors, records Checks, opens/resolves Incidents | done |
| SSL certificate checking | not built — fields exist on `Check` but I'm not populating them yet |
| Alerts (email/Slack/webhook when an incident opens or resolves) | not built — `alerts` app is just an empty shell right now |
| React frontend | not built |
| Real token/JWT auth (for the frontend to log in with) | not built — API currently uses Django session auth + basic auth, fine for me testing with curl, not fine for a real frontend |
| Multi-user teams / orgs / proper RBAC | not built — right now it's just "each user only sees their own monitors," no shared team workspaces |

## Branching rule I'm holding myself to

Every milestone or feature gets its own branch off `staging`. I never push straight to `main`:

```
milestone/or/feature branch → staging → main
```
