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
  api/          axios client + one file per resource (auth.js, monitors.js, checks.js, incidents.js, alerts.js)
  auth/         AuthContext (login/register/logout state), RequireAuth (route guard), tokens.js (localStorage)
  components/   pieces reused by a page but not routes themselves — CheckHistory, IncidentHistory,
                AlertChannels, StatusDot, MetricsBar, GoogleLoginButton
  pages/        one file per route — LoginPage, RegisterPage, MonitorsPage, MonitorDetailPage
  App.jsx       routes
  main.jsx      wraps App in BrowserRouter + AuthProvider + GoogleOAuthProvider
```

Same "split by concern" instinct as the backend — `api/` doesn't know anything about React, it's just functions that call endpoints and return data. `auth/` owns the token lifecycle. `pages/` just renders and calls into the other two. `components/` is new as of the monitor detail page - `CheckHistory` and `IncidentHistory` each have their own filter state and polling, so they earned their own files instead of living inline in `MonitorDetailPage`.

## Design system — status colors, the pulse/alert dots, metrics

Used Claude's `dataviz` skill for this instead of just picking colors that looked fine - it ships a validated default palette (colorblind-safe categorical hues, and a fixed status palette that's never reused for anything else) plus rules for how a dashboard should actually be built. `index.css` defines the palette as CSS custom properties - surfaces, ink (primary/secondary/muted text), and the four status colors (`good`/`warning`/`serious`/`critical`) - light mode in `:root`, dark mode under `prefers-color-scheme: dark`.

**`StatusDot`** is the one component every status indicator in the app goes through - the monitors table, the monitor detail header, `CheckHistory`'s per-row status, even `IncidentHistory` (reused with `upLabel="resolved"` / `downLabel="ongoing"` so an incident's ongoing/resolved state uses the exact same visual language as a monitor's up/down state, instead of inventing a second color scheme). Every dot ships with a text label next to it, never color alone - colorblind readers (and anyone glancing quickly) shouldn't have to distinguish red from green to know what's going on.

The two animations:
- **Up** — a calm 2-second outward-expanding ring (`status-pulse-ring`), meant to read as "alive and being watched," not urgent.
- **Down** — a tighter 1.1-second glow pulse (`status-pulse-alert`), meant to read as "needs attention" without being an actual flashing strobe. Deliberately kept well under 3Hz (WCAG's seizure-risk threshold) - urgency doesn't require speed that fast.

Both respect `prefers-reduced-motion` - a global rule in `index.css` collapses every animation to effectively-instant for anyone with that OS setting on, rather than each component needing its own check.

**`MetricsBar`** is the stat-tile row at the top of the monitors page (Monitors / Up / Down / Ongoing incidents) - the "clear metrics" a monitoring dashboard should lead with, following the skill's stat-tile contract (label + value, color only on the value, only when the number is actually notable - an "Up" tile isn't green when it's 0). "Ongoing incidents" comes from `/api/incidents/?resolved=false` with no monitor filter (had to make `monitorId` optional in `api/incidents.js` for this - it previously always required one).

## The JWT dance (this is the part I had to actually think through)

`src/api/client.js` is a single axios instance every API call goes through:

- **Request interceptor** — if there's an access token in `localStorage`, attach it as `Authorization: Bearer <token>` on the way out. This is why none of the page components ever manually add auth headers, it's automatic.
- **Response interceptor** — if a response comes back 401 (access token expired) *and* there's a refresh token *and* this isn't already a retry, it calls `/auth/token/refresh/`, stores the new access token, and replays the original request once. If the refresh itself fails (refresh token also expired), it clears everything and lets the failed request propagate — `RequireAuth` then bounces the user to `/login` because `isAuthenticated` reads "is there an access token in storage."

The refresh call uses a *separate* plain axios instance (`refreshClient`, no interceptors) — using the same intercepted `client` for the refresh request itself would risk a loop if the refresh endpoint ever also 401'd.

`AuthContext` doesn't decode or validate the JWT client-side — `isAuthenticated` is just "is there a token sitting in localStorage." If that token's actually expired or garbage, the very next API call 401s and the interceptor above handles it. Didn't see the point of duplicating expiry logic client-side when the API is the real source of truth anyway.

## Monitor detail page - the "real-time log" per monitor

Clicking a monitor's name (`/monitors/:id`) goes to `MonitorDetailPage`, which renders the monitor's config plus three panels:

- **`AlertChannels`** — add/list/delete where this monitor's incidents get sent (email/Slack/webhook). This existed on the backend for a while with no frontend at all - I'd been testing it with curl and the Django shell, which meant the feature was genuinely unusable for anyone but me. Same list-plus-form pattern as the monitors page itself, just scoped to one monitor.
- **`IncidentHistory`** — the outage timeline (started/resolved/cause/ongoing-or-not), filterable by resolved-state and date range.
- **`CheckHistory`** — the raw ping log (up/down, HTTP code, response time, SSL status, failure reason), filterable by up/down and date range, with a "Load more" button that follows DRF's pagination `next` link to page through older history without re-deriving query params myself.

`IncidentHistory` and `CheckHistory` poll their endpoint every 10 seconds so new data shows up without a manual refresh - this is the "real-time-ish" part. Deliberately didn't reach for WebSockets/Django Channels for this - polling every 10s is a lot less machinery for a check that only happens every 60s+ anyway, and it's an easy swap later if polling ever actually feels too slow. `AlertChannels` doesn't poll - channel config doesn't change on its own the way check/incident data does, so a manual refresh after add/delete is enough.

One wrinkle I had to handle: if you click "Load more" and pull in older pages, a naive auto-refresh would wipe that out by re-fetching just page 1 every 10 seconds. `CheckHistory` tracks a `viewingMore` flag and pauses its own polling once you've paged past "recent," with a "back to recent" button that resets and resumes it.

## Auth for protected monitors

The monitor creation form (`MonitorsPage`) has a collapsed `<details>` section, "Protected endpoint? (optional)" - expand it to pick an auth type (Basic/Bearer/API key) and enter the credential. Collapsed by default since most monitors don't need this and the form was already getting crowded.

The credential input is `type="password"` so it's masked while typing, and it's a genuine write-only value on the wire too - the backend never sends it back (see the `monitors` README for why). What the detail page shows instead is `has_auth_credential` - a boolean, rendered as "BEARER (credential stored)" or "none," never the actual value. There's no edit capability for this yet (or for any monitor field - the form only creates), which is a real gap, just not a new one specific to auth.

## Google login

`GoogleLoginButton` (in `components/`) wraps `@react-oauth/google`'s `GoogleLogin` component, dropped onto both `LoginPage` and `RegisterPage` - it's the same button either way, since the backend handles first-login-creates-the-account itself. `main.jsx` wraps the whole app in `GoogleOAuthProvider` with `VITE_GOOGLE_CLIENT_ID`, which is what lets `GoogleLogin` render at all.

On success, Google hands back a credential (an ID token) via `onSuccess`; that gets passed straight to `AuthContext.loginWithGoogle`, which posts it to `/api/auth/google/` and stores whatever comes back exactly like a normal login - the rest of the app has no idea whether a session came from a password or from Google.

The Client ID is not a secret - it's meant to end up in browser JS, that's how Google's own flow works - so it living in a `VITE_*` env var (which Vite bakes into the client bundle) is correct and expected. The Client *secret* stays backend-only and unused by this flow.

## What I actually verified works

Ran it in a real browser end to end, twice now:

1. Register → `/monitors` → add a monitor → it shows in the table → log out → log back in → the monitor's still there, still scoped to that user.
2. Click into a monitor's detail page → seeded a Check + Incident directly in the database (simulating the Celery engine actually running) → confirmed the page picked both up automatically within one poll cycle, with **no manual reload** → confirmed the down/up and ongoing/resolved filters actually change what's returned.

No console errors in either run.

For the design/theme pass: seeded a demo user with one up monitor (valid SSL cert, real expiry date) and one down monitor with an ongoing incident, logged in as them in a real (headless) browser, and screenshotted the dashboard in both light and dark mode (`page.newPage({ colorScheme })`) - metrics tiles, status dots, and the SSL badges all rendered correctly in both, zero console errors. Confirmed via `getComputedStyle` that the pulse/alert animations are actually applying (`status-pulse-ring` / `status-pulse-alert` with the right durations), not just present in the CSS and silently not firing.

For Google login specifically: confirmed `npm run build` succeeds, confirmed in a real (headless) browser that the actual Google-rendered button shows up on both pages with the correct Client ID embedded in its request, and confirmed the backend's `/api/auth/google/` correctly rejects a missing or garbage token (400 / 401). What I *couldn't* verify end-to-end is an actual successful sign-in - that needs a real Google account clicking through a real consent screen, which isn't something to automate. First real click also hit `[GSI_LOGGER]: The given origin is not allowed for the given client ID` in the console, which is Google's authorized-origins setting taking time to propagate (documented as up to a few hours), not a bug here - worth re-testing a real click once that's had time to settle, and worth a real look if it's still failing after that.

For `AlertChannels`: registered a fresh user, created a monitor, added a Slack channel, added a webhook channel, confirmed both show up in the table, deleted the Slack one, confirmed it's actually gone (not just hidden) - all in a real browser, zero console errors.

## What's not built yet

- Response-time charts (the data's there in `CheckHistory`, just rendered as a table, not a graph) - would follow the same `dataviz` skill, this just wasn't in scope for the "clear metrics" pass
- Build tooling beyond Vite's defaults — no path aliases, no component library, nothing fancy
- A manual light/dark toggle - it follows the OS setting (`prefers-color-scheme`) only, no in-app switch and no persisted preference
