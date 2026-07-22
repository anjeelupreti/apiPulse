# frontend — my notes

React app, scaffolded with Vite. Talks to the Django API purely over HTTP — nothing here touches Postgres or Redis directly, everything goes through `/api/...`.

## Running it

```bash
cd frontend
npm install
cp .env.example .env   # points at the backend, default is fine for local dev
npm run dev
```

Needs the backend actually running (`backend/README.md`) — this is just the UI, it has nothing to show without the API behind it.

## How it's laid out

```
src/
  api/          axios client + one file per resource (auth.js, monitors.js, checks.js, incidents.js)
  auth/         AuthContext (login/register/logout state), RequireAuth (route guard), tokens.js (localStorage)
  components/   pieces reused by a page but not routes themselves — CheckHistory, IncidentHistory
  pages/        one file per route — LoginPage, RegisterPage, MonitorsPage, MonitorDetailPage
  App.jsx       routes
  main.jsx      wraps App in BrowserRouter + AuthProvider
```

Same "split by concern" instinct as the backend — `api/` doesn't know anything about React, it's just functions that call endpoints and return data. `auth/` owns the token lifecycle. `pages/` just renders and calls into the other two. `components/` is new as of the monitor detail page - `CheckHistory` and `IncidentHistory` each have their own filter state and polling, so they earned their own files instead of living inline in `MonitorDetailPage`.

## The JWT dance (this is the part I had to actually think through)

`src/api/client.js` is a single axios instance every API call goes through:

- **Request interceptor** — if there's an access token in `localStorage`, attach it as `Authorization: Bearer <token>` on the way out. This is why none of the page components ever manually add auth headers, it's automatic.
- **Response interceptor** — if a response comes back 401 (access token expired) *and* there's a refresh token *and* this isn't already a retry, it calls `/auth/token/refresh/`, stores the new access token, and replays the original request once. If the refresh itself fails (refresh token also expired), it clears everything and lets the failed request propagate — `RequireAuth` then bounces the user to `/login` because `isAuthenticated` reads "is there an access token in storage."

The refresh call uses a *separate* plain axios instance (`refreshClient`, no interceptors) — using the same intercepted `client` for the refresh request itself would risk a loop if the refresh endpoint ever also 401'd.

`AuthContext` doesn't decode or validate the JWT client-side — `isAuthenticated` is just "is there a token sitting in localStorage." If that token's actually expired or garbage, the very next API call 401s and the interceptor above handles it. Didn't see the point of duplicating expiry logic client-side when the API is the real source of truth anyway.

## Monitor detail page - the "real-time log" per monitor

Clicking a monitor's name (`/monitors/:id`) goes to `MonitorDetailPage`, which renders the monitor's config plus two independent history panels:

- **`IncidentHistory`** — the outage timeline (started/resolved/cause/ongoing-or-not), filterable by resolved-state and date range.
- **`CheckHistory`** — the raw ping log (up/down, HTTP code, response time, failure reason), filterable by up/down and date range, with a "Load more" button that follows DRF's pagination `next` link to page through older history without re-deriving query params myself.

Both poll their endpoint every 10 seconds so new data shows up without a manual refresh - this is the "real-time-ish" part. Deliberately didn't reach for WebSockets/Django Channels for this - polling every 10s is a lot less machinery for a check that only happens every 60s+ anyway, and it's an easy swap later if polling ever actually feels too slow.

One wrinkle I had to handle: if you click "Load more" and pull in older pages, a naive auto-refresh would wipe that out by re-fetching just page 1 every 10 seconds. `CheckHistory` tracks a `viewingMore` flag and pauses its own polling once you've paged past "recent," with a "back to recent" button that resets and resumes it.

## What I actually verified works

Ran it in a real browser end to end, twice now:

1. Register → `/monitors` → add a monitor → it shows in the table → log out → log back in → the monitor's still there, still scoped to that user.
2. Click into a monitor's detail page → seeded a Check + Incident directly in the database (simulating the Celery engine actually running) → confirmed the page picked both up automatically within one poll cycle, with **no manual reload** → confirmed the down/up and ongoing/resolved filters actually change what's returned.

No console errors in either run.

## What's not built yet

- Response-time charts (the data's there in `CheckHistory`, just rendered as a table, not a graph)
- Build tooling beyond Vite's defaults — no path aliases, no component library, nothing fancy
- Real styling — this is intentionally plain right now, functional over polished
