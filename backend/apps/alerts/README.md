# alerts — my notes

This is the piece that actually tells me something broke, instead of the incident just sitting quietly in the database. Email, Slack, and webhook all actually send now.

## The models

**AlertChannel** — where to send a notification for a given monitor. `channel_type` is EMAIL / SLACK / WEBHOOK, `target` is whatever that channel needs (an email address for EMAIL, a webhook URL for the other two). I made this per-monitor rather than per-user because I might want different people/channels notified for different monitors eventually — a prod API probably pages me, a side project probably doesn't need to.

**Notification** — a log row for every send attempt, success or fail, with `error_message` if it failed. Added this after thinking about the annoying "why didn't I get an alert" debugging session I'd inevitably have without it — now I can just look at the table instead of guessing whether the email actually went out.

## tasks.py — notify_incident

```python
@shared_task
def notify_incident(incident_id, event):
    ...
```

Called from `incidents.services.evaluate_incident` for three events now: `opened`, `escalated` (added when I adapted Sentry's re-notify behavior — see the `incidents` README), and `resolved`. Always via `.delay()` so sending doesn't block the check/incident logic. It loops over every active `AlertChannel` for that monitor and, based on `channel_type`, looks up the right sender function from a small `SENDERS` dict and calls it. If `notify_incident` ever gets a `channel_type` with no entry in `SENDERS`, it logs a Notification with `success=False` and an explanatory `error_message` instead of silently doing nothing - that's dead code right now (all three model choices have senders), just left the safety net in since a fourth channel type is plausible later.

`_message(incident, event)` is a shared helper that picks the subject/body prose per event - `escalated` gets its own "is STILL down, ongoing since X" text rather than reusing `opened`'s, so a re-notify doesn't read like a duplicate. Both `_send_email` and `_send_slack` use it; `_send_webhook` doesn't, since a webhook's audience is a script parsing JSON, not a person reading prose - it gets structured `{event, monitor: {...}, incident: {...}}` instead.

- **Email** — `django.core.mail.send_mail`, Django's SMTP backend pointed at Gmail (`EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` in `.env`, an app password). Fine for now; I'll swap to a real transactional provider (SES, Postmark, etc.) before this is anything but my own dev setup.
- **Slack** — a plain `requests.post` to whatever incoming-webhook URL the user's `target` is, `{"text": "*subject*\nbody"}`. That's literally all a Slack incoming webhook needs.
- **Webhook** — same `requests.post`, JSON payload instead, for anything that wants to parse this programmatically (a script, Zapier, PagerDuty's generic webhook integration).

Both Slack and webhook call `response.raise_for_status()` after posting - without that, a webhook endpoint returning 404 or 500 would still count as a successful send, since `requests` doesn't raise on its own for non-2xx responses. Email doesn't need this - `send_mail` already raises on an SMTP failure.

## API routes

| Method | Path | Does what |
|---|---|---|
| GET / POST | `/api/alert-channels/` | list / create channels for my monitors (`?monitor={id}` to scope to one) |
| GET / PUT / PATCH / DELETE | `/api/alert-channels/{id}/` | manage one |
| GET | `/api/notifications/` | delivery log, read-only (?monitor={id} to filter) |

The serializer double-checks that the `monitor` I'm attaching a channel to is actually mine, even though the queryset already only shows my own monitors — being paranoid at the write path specifically, since that's the one place a bad ID could otherwise slip through.

## What I actually verified works

Ran the full loop by hand: opened an incident (3 failing checks in a row), confirmed a real email landed via Gmail SMTP with `success=True` in the Notification log, then fixed the monitor and confirmed the resolve email sent too. Also confirmed the `.delay()` call from `incidents.services` actually reaches a real Celery worker and completes — not just the synchronous path.

Later, for escalation specifically: backdated an ongoing incident's `started_at`/`last_escalated_at` in a shell test (rather than waiting 15 real minutes), ran it through a real Celery worker, and confirmed the full sequence logged correctly - `opened`, `escalated`, `escalated` again after backdating a second time, `resolved` - all four with `success=True`, and confirmed an *immediate* repeat check right after opening or escalating correctly sends nothing (the interval gate actually gates).

For Slack and webhook: pointed both a SLACK-type and a WEBHOOK-type channel at a real [webhook.site](https://webhook.site) test endpoint, triggered a real `opened` notification, and confirmed via webhook.site's own API that both payloads arrived exactly as expected - the Slack one as `{"text": "*subject*\nbody"}`, the webhook one as the structured JSON. Then pointed a channel at a deliberately unreachable host and confirmed the failure path logs `success=False` with the actual connection error as `error_message`, instead of silently swallowing it.

## What's not built here yet

- Any UI/API for "test this channel" without waiting for a real incident - right now you find out a channel's misconfigured when the incident it's supposed to be attached to actually fires
- Retries for failed sends — right now a failed send just logs `success=False` once and moves on, doesn't retry
