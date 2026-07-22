# frontend — my notes

Empty folder right now. Writing this so future-me remembers the plan instead of staring at a blank directory wondering where to start.

## What it's supposed to be

React, per the original architecture sketch — a dashboard that shows my monitors, their up/down status, response-time charts, and incident history. Talks to the Django backend purely over the REST API in `backend/` — nothing here talks to Postgres or Redis directly, everything goes through `/api/...`.

## How it'll talk to the backend

Plain HTTP requests to `http://127.0.0.1:8000/api/...` in dev (a real domain once deployed). CORS is already turned on for this on the backend side (`django-cors-headers`, wide open in `dev.py`, will need to be locked down to the actual frontend origin in `prod.py` once that's real).

Auth is the one thing that has to change before this can really work: the backend currently authenticates via Django session cookies or HTTP Basic auth, neither of which is right for a React app with its own login screen. Before writing much frontend code I'll need to add token or JWT auth to the backend (probably `djangorestframework-simplejwt` or DRF's built-in token auth) so the frontend can log in once and attach a token to every request instead.

Later, if I want live-updating status instead of polling, a WebSocket connection (Django Channels) is the natural next step — polling `/api/checks/` every few seconds is a fine starting point though, no need to build that on day one.

## What's not decided yet

- Build tooling — probably Vite, haven't committed to it
- State management — probably nothing fancy at first (React Query / plain fetch + hooks for server state), add Redux or similar only if it actually becomes painful without it
- Charting library for response-time graphs

## Setup instructions

Nothing to set up yet — there's no `package.json` here. This section gets filled in the moment I scaffold the actual React app.
