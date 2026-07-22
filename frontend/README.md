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
  api/          axios client + one file per resource (auth.js, monitors.js, checks.js, incidents.js, alerts.js, flags.js, admin.js)
  auth/         AuthContext (login/register/logout + user profile), RequireAuth, RequireStaff (route guards), tokens.js
  flags/        FlagsContext (fetch-once-per-login feature flag map) — same shape as auth/, different concern
  components/   pieces reused by a page but not routes themselves — CheckHistory, IncidentHistory,
                AlertChannels, StatusDot, MetricsBar, ResponseTimeChart, GoogleLoginButton
  pages/        one file per route — LoginPage, RegisterPage, MonitorsPage, MonitorDetailPage, AdminPage
  App.jsx       routes
  main.jsx      wraps App in BrowserRouter + AuthProvider + FlagsProvider + GoogleOAuthProvider
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

## Response-time chart

`ResponseTimeChart` sits above the checks table in `CheckHistory` - a hand-rolled SVG line chart, no charting library. Used the `dataviz` skill again to pick the form (trend over time, one series → line with a soft area wash, no legend needed since a single series' title already says what's plotted) and the interaction contract (a crosshair that snaps to the nearest point, one tooltip with the value bold and the timestamp secondary, same info reachable on keyboard focus + arrow keys as on hover).

Why hand-rolled instead of a library: it's one line, one area, a few gridlines, and a tooltip - maybe 100 lines of plain SVG + one `useState` for the hovered index. Didn't feel like reaching for Recharts or Chart.js was buying enough to be worth a new dependency and its bundle weight for a chart this simple. Only charts the most recent 30 points regardless of how much history is loaded elsewhere on the page - a giant multi-hundred-point line isn't more readable, it's just more DOM.

Nothing here gates on the chart - every value it plots is also sitting right there in the table underneath it, which is exactly what the skill means by "tooltips enhance, they never gate."

Verified in a real browser: seeded a monitor with 15 checks at deliberately varied response times, confirmed the rendered line's shape matches the table's numbers exactly, confirmed mouse hover produces the right tooltip (value + timestamp) at the nearest point, and confirmed keyboard focus + arrow keys move through the same points with the same tooltip info.

## Feature flags

`flags/FlagsContext.jsx` - same shape as `AuthContext`, but for feature flags instead of auth state. Wraps the app (inside `AuthProvider`, since it needs to know `isAuthenticated` before it can fetch anything), fetches `/api/flags/mine/` once per login, and exposes `useFlags()` returning `{ flags }` - a plain `{key: boolean}` map. `CheckHistory` is the one place that actually reads it so far: `flags['response-time-chart']` gates whether `ResponseTimeChart` renders at all, alongside the existing `results.length > 0` check.

Deliberately fetch-once-per-login, not polled - unlike check/incident data, a flag isn't expected to change mid-session, so re-fetching on an interval would just be wasted requests. If a flag actually needs to take effect faster than "next login," that's a future problem, not one worth solving speculatively now.

Verified in a real browser, all three states an admin could put a flag in: globally on → chart renders for a fresh login; globally off → chart doesn't render for a fresh login; globally off but granted to this one user specifically → chart renders for them. Confirmed by directly toggling the flag through the ORM between runs (same effect `/admin/` would have) rather than needing the admin UI to exist first.

## Admin section

`/admin` (the route, not Django's `/admin/`) - a staff-only page with a stats row (users/monitors/ongoing incidents/feature flags), a users table (deactivate/reactivate), and a feature-flags table (create, toggle globally-enabled, delete). Gated by a new `RequireStaff` guard, sitting alongside `RequireAuth` on the route - `RequireStaff` reads `user.is_staff` off `AuthContext`, which now also fetches `/api/accounts/me/` once per login (same fetch-once pattern as flags) so the frontend actually knows who's logged in beyond just "someone with a valid token."

`RequireStaff` has one subtlety: `user` starts `null` right after login, until the `/me/` fetch resolves. If it redirected on `user == null` the same as `!user.is_staff`, a real staff member would get bounced to `/monitors` for a split second on every fresh login before the truth caught up - so it renders a plain loading state while `user` is still `null`, and only redirects once it's actually resolved to non-staff. An "Admin" link in `MonitorsPage`'s header is conditionally rendered the same way, off `user?.is_staff`.

Same list-plus-form UI pattern as everywhere else in this app (`AlertChannels`, `MonitorsPage`'s form) - nothing new invented here, just applied to a different kind of data.

Verified in a real browser: registered a non-staff user, confirmed no Admin link appears and confirmed typing `/admin` in directly redirects to `/monitors` rather than showing anything. Logged in as staff, confirmed the link appears and the page shows real data matching the database. Exercised every action for real, not just the optimistic UI state - created a flag and confirmed it's actually in the table, toggled it on and confirmed the toggle persisted, deleted it and confirmed it's actually gone, deactivated a user and confirmed against the database that `is_active` flipped and that user's own login now 401s.

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

- Build tooling beyond Vite's defaults — no path aliases, no component library, nothing fancy
- A manual light/dark toggle - it follows the OS setting (`prefers-color-scheme`) only, no in-app switch and no persisted preference
