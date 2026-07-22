# frontend — my notes

React app, scaffolded with Vite. Talks to the Django API purely over HTTP — nothing here touches Postgres or Redis directly, everything goes through `/api/...`.

## Running it

```bash
cd frontend
npm install
cp .env.example .env   # points at the backend, default is fine for local dev
npm run dev
```

Needs the backend actually running (`backend/README.md`) — this is just the UI, it has nothing to show without the API behind it. Also needs `VITE_GOOGLE_CLIENT_ID` set in `.env` for the Google button to actually work (see the Google login section below) - without it, everything else still works fine, the button just won't.

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

## Google login

`GoogleLoginButton` (in `components/`) wraps `@react-oauth/google`'s `GoogleLogin` component, dropped onto both `LoginPage` and `RegisterPage` - it's the same button either way, since the backend handles first-login-creates-the-account itself. `main.jsx` wraps the whole app in `GoogleOAuthProvider` with `VITE_GOOGLE_CLIENT_ID`, which is what lets `GoogleLogin` render at all.

On success, Google hands back a credential (an ID token) via `onSuccess`; that gets passed straight to `AuthContext.loginWithGoogle`, which posts it to `/api/auth/google/` and stores whatever comes back exactly like a normal login - the rest of the app has no idea whether a session came from a password or from Google.

The Client ID is not a secret - it's meant to end up in browser JS, that's how Google's own flow works - so it living in a `VITE_*` env var (which Vite bakes into the client bundle) is correct and expected. The Client *secret* stays backend-only and unused by this flow.

## What I actually verified works

Ran it in a real browser end to end, twice now:

1. Register → `/monitors` → add a monitor → it shows in the table → log out → log back in → the monitor's still there, still scoped to that user.
2. Click into a monitor's detail page → seeded a Check + Incident directly in the database (simulating the Celery engine actually running) → confirmed the page picked both up automatically within one poll cycle, with **no manual reload** → confirmed the down/up and ongoing/resolved filters actually change what's returned.

No console errors in either run.

For Google login specifically: confirmed `npm run build` succeeds, confirmed in a real (headless) browser that the actual Google-rendered button shows up on both pages with the correct Client ID embedded in its request, and confirmed the backend's `/api/auth/google/` correctly rejects a missing or garbage token (400 / 401). What I *couldn't* verify end-to-end is an actual successful sign-in - that needs a real Google account clicking through a real consent screen, which isn't something to automate. First real click also hit `[GSI_LOGGER]: The given origin is not allowed for the given client ID` in the console, which is Google's authorized-origins setting taking time to propagate (documented as up to a few hours), not a bug here - worth re-testing a real click once that's had time to settle, and worth a real look if it's still failing after that.

## What's not built yet

- Response-time charts (the data's there in `CheckHistory`, just rendered as a table, not a graph)
- Build tooling beyond Vite's defaults — no path aliases, no component library, nothing fancy
- Real styling — this is intentionally plain right now, functional over polished
