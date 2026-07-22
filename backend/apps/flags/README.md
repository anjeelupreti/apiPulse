# flags — my notes

Feature flags: enable/disable a feature globally, or for specific users, without a deploy. First piece of the admin-panel work - decided to build this one first since the other two pieces (a React admin section, traffic analytics) both benefit from having somewhere to actually manage settings once they exist.

## The model

**FeatureFlag** — `key` (a slug, e.g. `response-time-chart` - just a string both backend and frontend agree on, not a Python enum I'd have to update in two places every time), `is_globally_enabled`, and `enabled_for_users` (a M2M for per-user overrides when it's not globally on).

`is_enabled(key, user=None)` is the one function anything should ever call - never query `FeatureFlag` directly elsewhere. The logic: globally enabled → True for everyone. Not globally enabled → True only if `user` is in `enabled_for_users`. Key doesn't exist at all → **False** (fail closed) - an unconfigured flag is not a flag that's on, by design, so a typo in a key string doesn't silently enable something.

That fail-closed default created a real question for the one flag I actually use it for (`response-time-chart`, gating the frontend chart from the previous milestone): that chart already shipped and works for everyone. If I just let a brand-new flag row not exist, fail-closed would mean the chart vanishes for every existing user the moment this migration runs - a regression, not a toggle. Fixed with a **data migration** (`0002_seed_response_time_chart_flag.py`) that creates the row already `is_globally_enabled=True` - so `is_enabled()` stays safely fail-closed as a general rule, while this specific already-shipped feature doesn't regress on day one.

## API routes

| Method | Path | Does what |
|---|---|---|
| GET | `/api/flags/mine/` | every flag, resolved to `true`/`false` for whoever's asking - `{"response-time-chart": true}` |
| GET/POST/PUT/PATCH/DELETE | `/api/admin/flags/` | full CRUD, **staff only** (`IsAdminUser`) |

Deliberately two different shapes for two different audiences: `/mine/` is what every logged-in user hits to decide what to render, and it only ever returns booleans - never who else has a flag, never the full `FeatureFlag` rows. `/api/admin/flags/` is the actual management surface and returns everything, but only staff can reach it at all.

The React admin section (`adminpanel` app + `frontend/src/pages/AdminPage.jsx`) now gives this a proper UI - create a flag, toggle `is_globally_enabled`, delete one. Django's `/admin/` (`filter_horizontal` for the user list) is still the only way to manage per-user grants though - that part of the UI didn't make it into the admin page's first pass, noted directly on the page itself.

## What I actually verified works

Backend: `is_enabled()` directly - unknown key is False, the seeded globally-enabled flag is True regardless of user, a fresh off-by-default flag is False, and granting it to one specific user makes it True for them and False for everyone else. Then the API: staff hitting `/api/admin/flags/` gets 200, a freshly registered non-staff user gets 403, and both get a correct `/api/flags/mine/` response.

Then in a real browser: logged in with the flag globally on, confirmed the response-time chart renders; turned it off via the ORM (same effect as an admin using `/admin/`), logged in fresh, confirmed the chart is gone; granted it to that one user specifically while leaving global off, confirmed the chart came back for them. All three states matched what `is_enabled()` should produce.

## What's not built here yet

- Per-user grant management in the React admin page - still Django `/admin/`-only for that specific action
- Nothing else in the app is actually gated yet - `response-time-chart` is the one real example; wiring up a new gate anywhere else is just `is_enabled('some-key', request.user)` on the backend or the same `flags['some-key']` pattern via `useFlags()` on the frontend
