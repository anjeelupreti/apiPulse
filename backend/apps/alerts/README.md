# alerts — my notes

Nothing's built here yet. This is a placeholder README so future-me remembers what this app is *for* before I actually build it.

## What this is supposed to do

Right now, when `incidents.services.evaluate_incident` opens or resolves an Incident, nothing happens except a row getting written to the database. Nobody gets told. The whole point of a monitoring tool is that it tells you when something breaks *without you having to go look* — so this app is where that notification logic is supposed to live.

## Rough plan for when I get here

- `AlertChannel` model — where to send notifications: email address, Slack webhook URL, generic webhook URL. Probably FK'd to `Monitor` (or maybe to `User`, haven't decided — depends whether alert preferences are per-monitor or per-account)
- Hook into `incidents.services.evaluate_incident` — when it opens or resolves an incident, fire off a Celery task (not send synchronously — same reasoning as the ping logic, don't want a slow email/Slack API call blocking anything) that notifies every `AlertChannel` for that monitor
- `Notification` model, maybe — a log of what was actually sent and when, mostly so I can debug "why didn't I get paged"

## Why I created the empty app now instead of waiting

Wanted it in `INSTALLED_APPS` and in the folder structure from the start, so when I do build it there's no restructuring — just filling in `models.py`, `tasks.py`, etc. in a spot that already exists.
