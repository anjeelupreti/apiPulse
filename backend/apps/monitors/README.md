# monitors — my notes

This app answers one question: **what am I watching, and how should it be checked?** It does not actually do any pinging — that's `checks`. This app is just the config.

## The Monitor model

| Field | What it's for |
|---|---|
| `owner` | FK to User — whoever created this monitor. Every query gets filtered by this, so users only ever see their own monitors. |
| `name` | just a label, e.g. "Prod health endpoint" |
| `url` | what to ping |
| `method` | GET / POST / HEAD — most health checks are GET, but some APIs only respond sensibly to HEAD |
| `check_interval_seconds` | how often to check it, e.g. every 60s |
| `timeout_seconds` | how long to wait before calling it a failure |
| `expected_status_code` | what "up" means for this monitor — defaults to 200, but if I'm monitoring something that's supposed to 401 without auth, I'd set that here |
| `is_active` | lets me pause a monitor without deleting its history |
| `last_checked_at` | when the engine last actually pinged this — this is how the scheduler (below) knows what's overdue |
| `current_status` (serializer only, not a DB column) | `'up'` / `'down'` / `null` (no checks yet) — the frontend's status dots run off this |

## tasks.py — the scheduler side of the engine

```python
@shared_task
def dispatch_due_checks():
    ...
```

Celery beat calls this every 15 seconds (the schedule lives in `config/settings/base.py`, `CELERY_BEAT_SCHEDULE`). All it does is loop over active monitors and, for each one, check: has `check_interval_seconds` passed since `last_checked_at`? If yes, queue a `checks.tasks.perform_check` job for it.

I went with "one dumb 15s tick that figures out who's due" instead of "schedule each monitor individually at its own interval" because the second approach means rewriting the Celery beat schedule (which is basically static config) every time a monitor is added, removed, or its interval changes. This way beat's config never has to change — the logic for "who's due" lives in normal Python/ORM code I can actually read and debug, not in Celery's scheduling internals.

One thing to know: this does one query for all active monitors, then loops in Python. Fine at the scale I'm at. If I ever have thousands of monitors this'll need to become a smarter DB query, but that's a someday problem.

## API routes

Standard DRF router, full CRUD, all scoped to `request.user`:

| Method | Path | Does what |
|---|---|---|
| GET | `/api/monitors/` | list my monitors (paginated) |
| POST | `/api/monitors/` | create one — `owner` gets set automatically from whoever's logged in, don't send it |
| GET | `/api/monitors/{id}/` | one monitor |
| PUT / PATCH | `/api/monitors/{id}/` | update |
| DELETE | `/api/monitors/{id}/` | delete — cascades, deletes its Checks and Incidents too |

Example:
```bash
curl -u me:pass -X POST http://127.0.0.1:8000/api/monitors/ \
  -H "Content-Type: application/json" \
  -d '{"name":"my api health","url":"https://api.example.com/health"}'
```

`current_status` on the serializer does `monitor.checks.order_by('-checked_at').first()` per monitor - one extra query per monitor in a list response, not prefetched. Fine at this scale (added it so the frontend dashboard doesn't need N separate requests just to show status dots); would want an annotate/prefetch if the monitor list ever gets large.
