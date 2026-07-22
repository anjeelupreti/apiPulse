# incidents — my notes

This app decides what counts as an "outage" and tracks it from start to resolution. `checks` just tells it "this ping succeeded or failed" — this app is the only place that decides whether that adds up to an incident.

## The Incident model

| Field | What it's for |
|---|---|
| `monitor` | which monitor this outage is for |
| `started_at` | set automatically when the row is created |
| `resolved_at` | null while ongoing, set the moment it recovers |
| `cause` | copied from whatever `failure_reason` was on the check that triggered it — just a hint, not authoritative |
| `last_escalated_at` | null until the first re-notify fires; tracks when I last actually told someone about this incident, opened or escalated |
| `is_ongoing` (property) | just `resolved_at is None`, not a real DB column |

## services.py — the actual open/resolve/escalate decision

```python
FAILURE_THRESHOLD = 3
ESCALATION_INTERVAL = timedelta(minutes=15)

def evaluate_incident(monitor, check):
    ...
```

This is called from `checks.tasks.perform_check` right after every single Check gets saved. The logic:

- **If the check succeeded** and there's an ongoing incident for this monitor → resolve it (stamp `resolved_at`), notify `resolved`. Done.
- **If the check failed** and there's already an ongoing incident → check how long it's been since `last_escalated_at` (or `started_at` if never escalated). If that's ≥ `ESCALATION_INTERVAL`, notify `escalated` and stamp `last_escalated_at`. Either way, don't open a second incident for the same outage.
- **If the check failed** and there's no ongoing incident → look at the last 3 checks for this monitor. Only if *all 3* failed do I actually open a new Incident, and notify `opened`.

That "3 in a row" threshold (`FAILURE_THRESHOLD`) is the important design decision for *opening* an incident. I didn't want a single blip — one dropped packet, one slow response that happened to time out — to immediately count as a full-blown incident.

The escalation piece is adapted from how Sentry handles ongoing issues: it doesn't send one alert and go silent on something still broken, it can re-notify. Without this, an outage that lasts 6 hours would generate exactly one email at the start and one at the end - nothing in between telling me it's *still* down. `ESCALATION_INTERVAL` (15 minutes) controls how often that repeats; there's no cap on how many times it can fire, since "still down" stays true and worth repeating for as long as it actually is.

Trade-off I'm accepting on detection speed: with a 60-second check interval and needing 3 failures, it takes up to ~2 minutes to detect an outage in the first place. If that ever feels too slow, the fix is either lowering `FAILURE_THRESHOLD` or lowering `check_interval_seconds` on the monitor — not touching this logic.

## API routes

Read-only, same reasoning as checks — incidents should only ever be created by the engine's own logic, never by a person hitting the API directly.

| Method | Path | Does what |
|---|---|---|
| GET | `/api/incidents/` | all incidents across my monitors |
| GET | `/api/incidents/?monitor={id}` | just one monitor's incident history |
| GET | `/api/incidents/?monitor={id}&resolved=false` | only ongoing incidents for that monitor |
| GET | `/api/incidents/?monitor={id}&since=...&until=...` | date range, filtered against `started_at` (when the outage began, not when it resolved) |
| GET | `/api/incidents/{id}/` | one specific incident |

## What's not built here yet

- A configurable rules engine - `FAILURE_THRESHOLD` and `ESCALATION_INTERVAL` are both hardcoded module constants, not something a user can tune per-monitor. Sentry lets you configure rules like this per-project; here it's the same value for every monitor everyone has.
- Verified escalation only by manually backdating `started_at`/`last_escalated_at` in a shell test, not by actually waiting 15 real minutes with the engine running - the logic is the same either way, just noting how it was checked.
