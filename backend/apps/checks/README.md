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
| `ssl_valid` | null if the URL isn't https (doesn't apply); otherwise whether the cert is currently trusted and unexpired |
| `ssl_expires_at` | when the cert expires - only known if we actually completed a handshake, so it's null whenever `ssl_valid` is False |

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
5. Separately, run `ssl_check.check_ssl_certificate(monitor.url)` - it's its own module, not folded into the request logic above
6. Write the `Check` row (HTTP result + SSL result together)
7. Update `monitor.last_checked_at` (this is what `monitors.tasks.dispatch_due_checks` reads to know what's overdue)
8. Hand off to `incidents.services.evaluate_incident(monitor, check)` — this app doesn't decide what an "outage" is, that's incidents' call entirely

I can call `perform_check(monitor_id)` directly (not `.delay()`) in the Django shell to test it synchronously without needing a Celery worker running at all — that's how I actually verified this logic while building it, way faster than waiting on real beat ticks.

## ssl_check.py — the cert inspection

Plain `socket` + `ssl` from the standard library, no new dependency. Connects to the host on 443, does a TLS handshake through `ssl.create_default_context()` (full hostname + trust-chain verification, same as any browser would do), and reads `notAfter` off the returned certificate to get the expiry. If the handshake fails for *any* reason - expired cert, wrong hostname, untrusted CA, host unreachable, whatever - I can't tell those apart from `ssl.SSLError`/`socket.error` alone, so it all collapses to `ssl_valid=False, ssl_expires_at=None`. Good enough to answer "is this cert fine or not," not detailed enough to say *why* it isn't - `failure_reason` on the check is still the HTTP layer's story, not the cert's.

One inefficiency I'm accepting: this opens a *second* TLS connection per check, separate from the one `requests` already made for the actual HTTP ping. Pulling the cert out of `requests`'/urllib3's internals instead would mean one handshake instead of two, but it means digging into library internals that could change between versions. At 60s+ check intervals this extra handshake is noise; if monitors ever got a lot more frequent it'd be worth revisiting.

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

## What's not built here yet

- SSL data now renders in the frontend (`CheckHistory`'s SSL column, part of the dashboard redesign) but still doesn't feed into incident detection - a monitor with an expiring/invalid cert but a correct HTTP response is still just "up" as far as `incidents` is concerned. Deliberately kept separate for now; "alert me before my cert expires" would be a real feature to add later, not something I backed into this quietly.
