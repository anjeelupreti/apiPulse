# alerts — my notes

This is the piece that actually tells me something broke, instead of the incident just sitting quietly in the database. Email is working now; Slack/webhook are modeled but not wired up yet.

## The models

**AlertChannel** — where to send a notification for a given monitor. `channel_type` is EMAIL / SLACK / WEBHOOK, `target` is whatever that channel needs (an email address for EMAIL, a webhook URL for the other two). I made this per-monitor rather than per-user because I might want different people/channels notified for different monitors eventually — a prod API probably pages me, a side project probably doesn't need to.

**Notification** — a log row for every send attempt, success or fail, with `error_message` if it failed. Added this after thinking about the annoying "why didn't I get an alert" debugging session I'd inevitably have without it — now I can just look at the table instead of guessing whether the email actually went out.

## tasks.py — notify_incident

```python
@shared_task
def notify_incident(incident_id, event):
    ...
```

Called from `incidents.services.evaluate_incident` for three events now: `opened`, `escalated` (added when I adapted Sentry's re-notify behavior — see the `incidents` README), and `resolved`. Always via `.delay()` so sending the email doesn't block the check/incident logic. It loops over every active `AlertChannel` for that monitor and, based on `channel_type`, looks up the right sender function from a small `SENDERS` dict and calls it. Only `EMAIL` has a sender right now — if someone creates a SLACK or WEBHOOK channel, `notify_incident` still runs, just logs a Notification with `success=False` and an explanatory `error_message` instead of silently doing nothing. That felt better than pretending those channel types don't exist in the model at all.

`_send_email` picks the subject/body per event — `escalated` gets its own "is STILL down, ongoing since X" message rather than reusing the `opened` text, so a re-notify email doesn't read like a duplicate of the first one.

Email itself is just `django.core.mail.send_mail` — nothing fancy, using Django's SMTP backend pointed at Gmail (`EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` in `.env`, an app password, not a real account password since Gmail requires that once 2FA's on). Fine for now; I'll swap to a real transactional provider (SES, Postmark, etc.) before this is anything but my own dev setup — noting that so I don't forget Gmail SMTP has sending limits that'll matter the moment this isn't just me testing.

## API routes

| Method | Path | Does what |
|---|---|---|
| GET / POST | `/api/alert-channels/` | list / create channels for my monitors |
| GET / PUT / PATCH / DELETE | `/api/alert-channels/{id}/` | manage one |
| GET | `/api/notifications/` | delivery log, read-only (?monitor={id} to filter) |

The serializer double-checks that the `monitor` I'm attaching a channel to is actually mine, even though the queryset already only shows my own monitors — being paranoid at the write path specifically, since that's the one place a bad ID could otherwise slip through.

## What I actually verified works

Ran the full loop by hand: opened an incident (3 failing checks in a row), confirmed a real email landed via Gmail SMTP with `success=True` in the Notification log, then fixed the monitor and confirmed the resolve email sent too. Also confirmed the `.delay()` call from `incidents.services` actually reaches a real Celery worker and completes — not just the synchronous path.

Later, for escalation specifically: backdated an ongoing incident's `started_at`/`last_escalated_at` in a shell test (rather than waiting 15 real minutes), ran it through a real Celery worker, and confirmed the full sequence logged correctly - `opened`, `escalated`, `escalated` again after backdating a second time, `resolved` - all four with `success=True`, and confirmed an *immediate* repeat check right after opening or escalating correctly sends nothing (the interval gate actually gates).

## What's not built here yet

- Slack and webhook senders (model supports them, `SENDERS` dict doesn't have entries for them yet)
- Any UI/API for "test this channel" without waiting for a real incident
- Retries for failed sends — right now a failed send just logs `success=False` once and moves on, doesn't retry
