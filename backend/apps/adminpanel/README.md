# adminpanel — my notes

The other two pieces of the admin-panel work I split out earlier: a real user list with the ability to deactivate someone, and a stats summary. Feature flags (previous milestone, `flags` app) already had a staff-only API; this app is where the rest of the cross-cutting admin data lives.

## Why a separate app instead of putting this in `accounts`

A "list all users with their monitor count" view genuinely spans two apps (`accounts` for the users, `monitors` for the count) - it doesn't belong to either one specifically. Same for stats, which pulls from `accounts`, `monitors`, `incidents`, and `flags` all at once. Rather than force this into whichever app "felt closest," I gave it its own home. No models of its own - it's pure aggregation over data other apps already own.

Named `adminpanel`, not `admin` - Django's own built-in admin app is already called `admin`, and shadowing that name would be a genuinely confusing bug waiting to happen.

## The endpoints

| Method | Path | Does what |
|---|---|---|
| GET | `/api/admin/stats/` | `{total_users, total_monitors, total_ongoing_incidents, total_feature_flags}` - staff only |
| GET | `/api/admin/users/` | every user, with `monitor_count` computed per-user - staff only |
| GET | `/api/admin/users/{id}/` | one user |
| PATCH | `/api/admin/users/{id}/` | **only `is_active` is writable** - see below |

`AdminUserViewSet` deliberately only mixes in `ListModelMixin`, `RetrieveModelMixin`, `UpdateModelMixin` - no create, no destroy. This panel manages *existing* accounts; it was never meant to be where new users get created (that's registration) or deleted (didn't want a one-click "delete this person's entire account and every monitor they own" button existing at all yet, let alone in a first pass).

`AdminUserSerializer` marks everything except `is_active` as `read_only_fields` - `username`, `email`, and especially `is_staff` can't be changed through this endpoint even if someone crafts the PATCH body by hand. Promoting someone to staff is a `manage.py`/Django-admin action on purpose, not a button in this panel - that felt like too consequential an action to expose casually in a v1.

## Also added this milestone: `GET /api/accounts/me/`

Lives in `accounts`, not here, since it's about identity, not admin data - but it's what makes any of this possible on the frontend. Returns `{id, username, email, is_staff}` for whoever's making the request. The frontend needed *some* way to know "is the logged-in person staff" to decide whether to show the Admin link and gate the `/admin` route at all - decoding the JWT client-side to look for a staff claim felt like the wrong layer to put that decision in, so it's just another API call, same reasoning as feature flags (ask the API, don't decode the token yourself).

## What I actually verified works

Backend: `/me/` correctly reports `is_staff` for both a staff and a freshly-registered non-staff user. `/api/admin/users/` and `/api/admin/stats/` both 403 for non-staff, 200 with correct data for staff. PATCH-ing `is_active=false` actually works, and PATCH-ing `is_staff`/`username` in the same request is silently ignored (read-only fields hold). Confirmed the deactivation has real teeth too - the deactivated user's own Basic-auth request against `/me/` immediately starts returning 401.

Then in a real browser: registered a non-staff user, confirmed no "Admin" link appears in the header and confirmed navigating straight to `/admin` by URL redirects them to `/monitors` instead of showing anything. Logged in as staff, confirmed the Admin link does appear, and exercised every action on the page for real - created a flag, toggled it on, deleted it, deactivated a user - each one checked against the database afterward, not just the UI's optimistic state.

## What's not built here yet

- Promoting a user to staff, or deleting a user entirely - both deliberately excluded from this panel, not just unbuilt
- Per-user feature flag grants aren't editable from this UI (Django's `/admin/` still needed for that) - noted directly on the page itself so it's not a silent gap
- Any of this data is a live snapshot on page load - no polling, no live updates. Fine for now; an admin checking in occasionally doesn't need real-time.
