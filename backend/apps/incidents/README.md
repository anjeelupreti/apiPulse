# incidents — my notes

This app decides what counts as an "outage" and tracks it from start to resolution. `checks` just tells it "this ping succeeded or failed" — this app is the only place that decides whether that adds up to an incident.

## The Incident model

| Field | What it's for |
|---|---|
| `monitor` | which monitor this outage is for |
| `started_at` | set automatically when the row is created |
| `resolved_at` | null while ongoing, set the moment it recovers |
| `cause` | copied from whatever `failure_reason` was on the check that triggered it — just a hint, not authoritative |
| `is_ongoing` (property) | just `resolved_at is None`, not a real DB column |

## services.py — the actual open/resolve decision

```python
FAILURE_THRESHOLD = 3

def evaluate_incident(monitor, check):
    ...
```

This is called from `checks.tasks.perform_check` right after every single Check gets saved. The logic:

- **If the check succeeded** and there's an ongoing incident for this monitor → resolve it (stamp `resolved_at`). Done.
- **If the check failed** and there's already an ongoing incident → do nothing, it's the same outage continuing, don't open a second one.
- **If the check failed** and there's no ongoing incident → look at the last 3 checks for this monitor. Only if *all 3* failed do I actually open a new Incident.

That "3 in a row" threshold (`FAILURE_THRESHOLD`) is the important design decision here. I didn't want a single blip — one dropped packet, one slow response that happened to time out — to immediately count as a full-blown incident. Requiring 3 consecutive failures means it takes an actual sustained outage before anything gets recorded, which matters a lot once alerts (see the `alerts` app) start pinging me every time an incident opens.

Trade-off I'm accepting: with a 60-second check interval and needing 3 failures, it takes up to ~2 minutes to detect an outage. If that ever feels too slow, the fix is either lowering `FAILURE_THRESHOLD` or lowering `check_interval_seconds` on the monitor — not touching this logic.

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

- Escalation - right now an incident sends exactly one "opened" email and one "resolved" email (see `alerts`), no matter how long the outage drags on. No "still down after an hour, nag me again" behavior. This is the Sentry-style pattern I want to adapt next: they don't just group and notify once, they can re-notify on rules like "seen again after being resolved" or "still happening N minutes later."
- A configurable rules engine - the "3 in a row" threshold is hardcoded, not something a user can tune per-monitor.
