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
  api/          axios client + one file per resource (auth.js, monitors.js)
  auth/         AuthContext (login/register/logout state), RequireAuth (route guard), tokens.js (localStorage)
  pages/        one file per route — LoginPage, RegisterPage, MonitorsPage
  App.jsx       routes
  main.jsx      wraps App in BrowserRouter + AuthProvider
```

Same "split by concern" instinct as the backend — `api/` doesn't know anything about React, it's just functions that call endpoints and return data. `auth/` owns the token lifecycle. `pages/` just renders and calls into the other two.

## The JWT dance (this is the part I had to actually think through)

`src/api/client.js` is a single axios instance every API call goes through:

- **Request interceptor** — if there's an access token in `localStorage`, attach it as `Authorization: Bearer <token>` on the way out. This is why none of the page components ever manually add auth headers, it's automatic.
- **Response interceptor** — if a response comes back 401 (access token expired) *and* there's a refresh token *and* this isn't already a retry, it calls `/auth/token/refresh/`, stores the new access token, and replays the original request once. If the refresh itself fails (refresh token also expired), it clears everything and lets the failed request propagate — `RequireAuth` then bounces the user to `/login` because `isAuthenticated` reads "is there an access token in storage."

The refresh call uses a *separate* plain axios instance (`refreshClient`, no interceptors) — using the same intercepted `client` for the refresh request itself would risk a loop if the refresh endpoint ever also 401'd.

`AuthContext` doesn't decode or validate the JWT client-side — `isAuthenticated` is just "is there a token sitting in localStorage." If that token's actually expired or garbage, the very next API call 401s and the interceptor above handles it. Didn't see the point of duplicating expiry logic client-side when the API is the real source of truth anyway.

## What I actually verified works

Ran it in a real browser end to end: register a new user → redirected to `/monitors` → add a monitor → it shows in the table → log out → log back in with the same credentials → the monitor's still there and still scoped to that user (didn't leak from/to any other account). No console errors.

## What's not built yet

- Anything showing Check/Incident history — right now the dashboard only shows the Monitor list itself, not its up/down history or response-time charts
- Any polling/live updates — the monitor list loads once on page mount, doesn't refresh itself while you're looking at it
- Build tooling beyond Vite's defaults — no path aliases, no component library, nothing fancy
- Real styling — this is intentionally plain right now, functional over polished
