# PulseWatch (apiPulse) — my notes

This is my API monitoring / uptime project. The idea: I register a URL, the system pings it on a schedule, logs what happened, and opens an incident if it starts failing repeatedly.

I'm writing this doc mostly for myself, so that when I come back to this in a few weeks I remember *why* things are structured this way, not just *what* the code does. Each folder has its own README going deeper into that piece — this one is just the map.

## How I'm thinking about the architecture

```
                    ┌──────────────┐
                    │   Browser    │   frontend/ — React (Vite)
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

    (same worker, once it writes a Check that opens/resolves an Incident,
     also queues alerts.tasks.notify_incident -> sends an email via Gmail SMTP)
```

The thing I had to get straight in my head: there are **two completely separate things** touching the database, on two separate rhythms.

1. **Me, through the API.** I hit `POST /api/monitors/` to register a URL. Totally normal request/response, nothing special.
2. **The monitoring engine, running in the background, on its own clock.** Every 15 seconds, **Celery beat** wakes up and asks "which monitors are due for a check?" (beat itself does zero real work — it's just a scheduler). For each monitor that's due, it drops a job onto a **Redis** queue. A separate process, the **Celery worker**, is the one actually pulling jobs off that queue, pinging the real URL, and writing the result — and if that result opens or resolves an Incident, the same worker queues another job to actually send the email.

Why not just ping the URL directly inside the Django view when someone hits the API? Because pinging some random external URL can be slow or hang entirely (timeouts, DNS issues, whatever) — and I don't want *my* API to freeze up because *someone else's* server is slow. Same reasoning for emails — SMTP can be slow too, so sending happens as its own queued job, not inline while the incident logic runs.

## Where I put things

```
apiPulse/
├── backend/        Django + DRF — see backend/README.md
│   └── apps/
│       ├── accounts/   who's logged in
│       ├── monitors/   what I'm watching (+ the scheduler task)
│       ├── checks/     the ping results (+ the actual ping task)
│       ├── incidents/  outage tracking (+ open/resolve logic)
│       └── alerts/     email notifications (Slack/webhook modeled, not sending yet)
├── frontend/       React dashboard — login/register + monitor list+create, see frontend/README.md
└── deployment/     docker-compose for Postgres/Redis
```

I split these into separate Django apps on purpose, one concern each, instead of dumping everything into one giant app. The rule I'm following: `monitors` doesn't know *how* to ping a URL, it just holds the config and hands off to `checks`. `checks` doesn't decide what counts as an "outage," it just records what happened and hands off to `incidents`. That way when I'm confused about a bug, I only have to hold one app's logic in my head at a time.

## How I run this locally

1. **Spin up Postgres + Redis**: `cd deployment && docker compose up -d`
2. **API server**: set up the venv in `backend/` (see backend/README.md), then `python manage.py runserver`
3. **Monitoring engine** (only needed if I actually want checks to run): start a Celery worker + Celery beat, both documented in backend/README.md
4. **Frontend**: `cd frontend && npm install && cp .env.example .env && npm run dev` — see frontend/README.md

## What's actually done vs. what I still owe myself

| Piece | Status |
|---|---|
| Custom User model, Postgres, env-based settings | done |
| Monitor CRUD API | done |
| Celery engine — pings monitors, records Checks, opens/resolves Incidents | done |
| SSL certificate checking | not built — fields exist on `Check` but I'm not populating them yet |
| Email alerts on incident open/resolve/escalate | done — Gmail SMTP, verified all three fire correctly and that the escalation interval actually gates repeat sends |
| Slack / webhook alerts | not built — `AlertChannel` model supports the types, no sender written yet |
| React frontend | in progress — auth, monitor list+create, and a per-monitor detail page with a filterable, auto-refreshing check/incident history, all verified in a real browser. No charts yet, no Google login |
| Registration + JWT auth | done — `/api/accounts/register/`, `/api/auth/token/`, verified a fresh user only ever sees their own monitors |
| Google login | not built yet — decided on approach (frontend Google Identity Services -> backend verifies ID token -> issues our own JWT), needs a Google Cloud OAuth Client ID before I can build it |
| Incident escalation (re-notify if still down after N minutes) | done — adapted from how Sentry avoids emailing once and going silent for a still-broken issue; `ESCALATION_INTERVAL = 15min`, no cap on repeat count |
| Multi-user teams / orgs / proper RBAC | not built — right now it's just "each user only sees their own monitors," no shared team workspaces |
| Admin panel (React admin section, feature flags, traffic/usage analytics) | not built — decided to scope this as its own set of milestones rather than one big undertaking |

## Branching rule I'm holding myself to

Every milestone or feature gets its own branch off `staging`. I never push straight to `main`:

```
milestone/or/feature branch → staging → main
```
