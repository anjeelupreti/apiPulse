# checks — my notes

This app is the "did the ping succeed" half of the engine. `monitors` decides *what's due*, this app does the actual work of pinging it and writing down what happened.

## The Check model

One row per ping, ever. Never updated after it's created — if I want history, I just look at all the rows for a monitor ordered by `checked_at`.

| Field | What it's for |
|---|---|
| `monitor` | which monitor this ping was for |
| `is_up` | the actual verdict — did the response match what the monitor expected |
| `status_code` | what the server actually returned (could be null if the request never got a response at all — timeout, DNS failure, etc.) |
| `response_time_ms` | how long the request took |
| `failure_reason` | human-readable reason if `is_up` is False — timeout, wrong status code, connection error |
| `ssl_valid`, `ssl_expires_at` | **not populated yet.** I added the columns because the original spec included SSL status, but I haven't written the cert-checking code. Todo. |

I made this append-only on purpose — it's going to be by far the highest-volume table (a row every N seconds per monitor, forever), and append-only tables are simpler to reason about and much easier to eventually partition/archive than ones with updates scattered through their history.

## tasks.py — perform_check, the actual ping

```python
@shared_task
def perform_check(monitor_id):
    ...
```

Step by step, what this does when Celery hands it a monitor_id:

1. Look up the Monitor (bail out quietly if it's been deleted or deactivated since it was queued — no point pinging something that's gone)
2. Send the actual HTTP request using `requests`, timing how long it takes
3. Compare the returned status code against `monitor.expected_status_code` — that comparison *is* the up/down verdict, not just "did it respond at all"
4. Catch timeouts and connection errors specifically, so `failure_reason` says something useful instead of a raw stack trace
5. Write the `Check` row
6. Update `monitor.last_checked_at` (this is what `monitors.tasks.dispatch_due_checks` reads to know what's overdue)
7. Hand off to `incidents.services.evaluate_incident(monitor, check)` — this app doesn't decide what an "outage" is, that's incidents' call entirely

I can call `perform_check(monitor_id)` directly (not `.delay()`) in the Django shell to test it synchronously without needing a Celery worker running at all — that's how I actually verified this logic while building it, way faster than waiting on real beat ticks.

## API routes

Read-only — I never want to manually create a Check through the API, only the engine should be writing these.

| Method | Path | Does what |
|---|---|---|
| GET | `/api/checks/` | all checks across my monitors, newest first |
| GET | `/api/checks/?monitor={id}` | just one monitor's history |
| GET | `/api/checks/?monitor={id}&is_up=false` | only the failures for that monitor |
| GET | `/api/checks/?monitor={id}&since=...&until=...` | date range, either end optional (ISO datetimes, filtered against `checked_at`) |
| GET | `/api/checks/{id}/` | one specific check |

Added the `since`/`until`/`is_up` filters for the monitor detail page in the frontend - it shows a "recent checks" log per monitor with filter controls, and this is what powers them. Kept the filtering logic as plain `if` checks parsing query params in the viewset rather than pulling in `django-filter` - three optional params didn't feel like enough to justify a new dependency.
