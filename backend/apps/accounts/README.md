# accounts — my notes

This app owns `User` (the `AUTH_USER_MODEL`) plus, now, actually signing up and logging in.

## Why this app exists even though User is empty

`User` is just `AbstractUser` with nothing added — no extra fields. So on paper it does nothing Django's built-in `auth.User` doesn't already do.

I made a custom one anyway, day one, before writing any other code: swapping `AUTH_USER_MODEL` after you've got real data in the default `auth.User` table means hand-writing a data migration — genuinely painful. Setting it up now, while the table's empty, costs nothing. So the model itself is still just future-proofing (I'll probably add something like `organization` or a plan/tier eventually) — the actual work in this app right now is the two things below.

## Registration

`POST /api/accounts/register/` — open to anyone (`AllowAny`), takes `username`, `email`, `password`. Runs the password through Django's normal `validate_password` (same rules as the admin — minimum length, not too common, not all-numeric, etc.) before creating the user. This is a plain DRF `CreateAPIView`, nothing clever.

Before this existed the only way to create a user was `manage.py createsuperuser` or `/admin/` — fine for me, useless for an actual frontend where someone else needs to sign up.

## Logging in — JWT

This is the part I had to actually think through. The API was already reachable via Django session auth (cookie, works if you're logged into `/admin/`) and HTTP Basic auth (fine for curl, not fine for a real app). Neither works for a React frontend with its own login form — a frontend can't "log into a Django session" the way a browser hitting `/admin/` does, and nobody should be sending a raw username/password on every single request the way Basic auth does.

JWT solves that: log in once, get back a token, attach that token to every request after.

```
POST /api/auth/token/           {"username": "...", "password": "..."}
  -> {"access": "...", "refresh": "..."}

then on every request:
  Authorization: Bearer <access token>

POST /api/auth/token/refresh/   {"refresh": "..."}
  -> {"access": "..."}   (new access token, once the old one expires)
```

Access tokens last 1 hour, refresh tokens last 1 day (`SIMPLE_JWT` in `config/settings/base.py`) — arbitrary values I picked, not tuned for anything specific yet. When the frontend exists, the plan is: store the access token in memory, use the refresh token to get a new one silently when it expires, and only force a real re-login once the refresh token itself expires.

I kept `SessionAuthentication` and `BasicAuthentication` in `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']` alongside JWT rather than replacing them — session auth is what makes the DRF browsable API (`/api/monitors/` in an actual browser, logged into `/admin/`) still work, and Basic auth is just convenient for me testing with curl. All three can coexist; DRF tries each in order and uses whichever one actually matches the request.

## What's not built here yet

- Logout / token blacklisting (right now a refresh token is valid until it naturally expires — no way to force-invalidate one early, e.g. if a token leaked)
- Password reset flow
- Any notion of teams/organizations — still just individual users, each seeing only their own monitors (enforced in the `monitors` app, not here)
