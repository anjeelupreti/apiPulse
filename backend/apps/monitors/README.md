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
| `auth_type` | NONE / BASIC / BEARER / API_KEY — how to authenticate against this URL when pinging it |
| `auth_header_name` | only used for API_KEY — which header to put the key in, e.g. `X-API-Key` |
| `auth_credential_encrypted` | the actual secret (a token, an API key, `username:password` for BASIC) - **encrypted at rest**, see below |

## Auth for protected endpoints

Came up when I was asked "what happens if the URL needs login?" - answer at the time was "nothing, it just pings anonymously and reads as down." That's fixed now: a monitor can carry `auth_type` + credentials, and `perform_check` sends them along.

The real decision here wasn't the HTTP mechanics (that part's easy - `requests` already knows how to do Basic auth, bearer tokens are just a header, API keys are just a header with a different name). It was **how to store someone's API key/token in my database without it sitting there in plain text.** Went with:

- **Symmetric encryption (Fernet, from the `cryptography` library), not hashing.** Hashing is one-way - fine for passwords I only ever need to *compare*, wrong here because `perform_check` needs the actual credential back to put it on the outgoing request. `monitors/crypto.py` is two functions, `encrypt`/`decrypt`, using a key from `FIELD_ENCRYPTION_KEY` in `.env`.
- **A model property, not a real field.** `Monitor.auth_credential` is a Python `@property` - reading it decrypts `auth_credential_encrypted` on the fly, setting it encrypts and stores. The rest of the codebase (`build_auth_kwargs`, the admin, tests) just uses `monitor.auth_credential` like it's a normal attribute and never has to think about encryption directly.
- **Rolled it by hand instead of a `django-encrypted-fields`-style package.** Same reasoning as everywhere else in this project - it's one function each way, nothing to learn beyond "here's the key, here's the ciphertext," and one fewer third-party dependency to trust with something this sensitive.
- **Never returned through the API, ever.** The serializer's `auth_credential` field is `write_only=True` - you can set it, you can never read it back, not even as your own monitor's owner. `has_auth_credential` (a boolean) is how the frontend shows "yes, something's configured" without the value ever leaving the server. This mirrors how Django itself never gives you a password back, just whether one's set.

`Monitor.build_auth_kwargs()` turns the config into whatever `requests.request(**kwargs)` needs - `{'auth': HTTPBasicAuth(...)}` for BASIC, `{'headers': {'Authorization': 'Bearer ...'}}` for BEARER, `{'headers': {<header name>: ...}}` for API_KEY, `{}` for NONE. `checks/tasks.py` just splats this into its existing `requests.request()` call.

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

## What I actually verified for the auth-header work

Encryption round-trip: stored ciphertext is never equal to the plaintext, and reading `monitor.auth_credential` back after a fresh `refresh_from_db()` gives the original value. Confirmed the serializer never includes `auth_credential` in its output regardless of request, while `has_auth_credential` correctly flips to `True` once one's set.

Then, against a real header-echoing test service (postman-echo.com), confirmed all three auth types actually arrive on the wire as expected: `Authorization: Bearer <token>` for BEARER, a custom header with the right name and value for API_KEY, and a correctly base64-encoded `Authorization: Basic <...>` for BASIC. Also verified end-to-end in a real browser: filled the auth fields in on the monitor creation form, created the monitor, and confirmed the detail page shows "BEARER (credential stored)" while the actual token string appears nowhere in the rendered page.

## What's not built here yet

- No way to *edit* an existing monitor's config through the UI at all yet (not just auth - name, URL, interval, none of it) - the form only creates. Editing auth specifically would need the same write-only-on-write care as creation.
- `auth_header_name` and `auth_credential` aren't validated against `auth_type` - you could in theory PATCH `auth_type=NONE` while leaving an old encrypted credential sitting in the DB unused. Harmless (it's never read when `auth_type` is NONE) but a little untidy.
