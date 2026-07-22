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

    (same worker, once it writes a Check that opens/resolves/escalates an
     Incident, also queues alerts.tasks.notify_incident -> fans out to
     whatever AlertChannels are configured: email via Gmail SMTP, Slack
     via an incoming webhook, or a generic webhook with structured JSON)
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
│       ├── alerts/     email/Slack/webhook notifications on incident open/resolve/escalate
│       ├── flags/      feature flags, global or per-user
│       └── adminpanel/ cross-cutting admin data (users, stats) for the admin section
├── frontend/       React dashboard — auth, monitor management, admin section, see frontend/README.md
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
| SSL certificate checking | done — verified against a real cert and an unreachable host; shown in the frontend now too; still doesn't feed into incident detection |
| Email/Slack/webhook alerts on incident open/resolve/escalate | done — verified email via Gmail SMTP, Slack + webhook against a real webhook.site endpoint (success and failure paths both), and that the escalation interval actually gates repeat sends |
| React frontend | in progress — auth (password + Google), monitor list+create (incl. auth-header config), a per-monitor detail page with filterable check/incident history, alert-channel management, and a response-time chart, plus a real dashboard theme (status colors, pulse/alert animations, metrics tiles) built with the `dataviz` skill |
| Registration + JWT auth | done — `/api/accounts/register/`, `/api/auth/token/`, verified a fresh user only ever sees their own monitors |
| Google login | built, not yet confirmed with a real click — `/api/auth/google/` verifies the ID token and issues our own JWT pair; button renders correctly with the right Client ID, but Google's authorized-origins setting needs time to propagate before an actual sign-in can be tested |
| Incident escalation (re-notify if still down after N minutes) | done — adapted from how Sentry avoids emailing once and going silent for a still-broken issue; `ESCALATION_INTERVAL = 15min`, no cap on repeat count |
| Auth headers for monitored URLs (Basic/Bearer/API key) | done — credentials encrypted at rest (Fernet), never returned through the API even to their own owner; verified against a real header-echoing test service for all three types |
| Response-time chart | done — hand-rolled SVG line chart (no charting library), crosshair + tooltip, keyboard-navigable; verified the rendered shape matches the underlying data exactly |
| Multi-user teams / orgs / proper RBAC | not built — right now it's just "each user only sees their own monitors," no shared team workspaces |
| Feature flags (global + per-user) | done — `/api/flags/mine/` (everyone) + `/api/admin/flags/` (staff CRUD); one real gate wired up (`response-time-chart`); verified all three states (global on/off, per-user override) actually change what renders |
| Admin section (users, stats, feature flags) | done — a real staff-only `/admin` page in the app itself, not just Django's `/admin/`; deactivate/reactivate users, manage flags; verified staff-vs-non-staff access control and every action against the database, not just the UI |
| Traffic/usage analytics | not built yet — last piece of the admin-panel epic |

## Branching rule I'm holding myself to

Every milestone or feature gets its own branch off `staging`. I never push straight to `main`:

```
milestone/or/feature branch → staging → main
```
