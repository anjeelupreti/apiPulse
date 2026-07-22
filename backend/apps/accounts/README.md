# accounts — my notes

This app owns exactly one thing: `User`. It's the `AUTH_USER_MODEL`.

## Why this app exists when User is empty

Right now `User` is just `AbstractUser` with nothing added — no extra fields, nothing. So on paper this app does nothing Django's built-in `django.contrib.auth.User` doesn't already do.

The reason I made a custom one anyway, day one, before writing any other code: if you ever want to add fields to User later (which I will — at minimum I'll want something like an `organization` or plan/tier at some point), Django makes that a genuine pain if you didn't set `AUTH_USER_MODEL` to a custom model from the very first migration. Once you've got real data in the default `auth.User` table, swapping it out means hand-writing a data migration. Setting it up now, while the table is empty, costs me nothing. So — no routes, no real logic here yet, just future-proofing.

## What's actually here

- `models.py` — the empty `User(AbstractUser)` subclass
- `admin.py` — registers it with Django's admin using the standard `UserAdmin` (so `/admin/` still gives me the normal "manage users, set permissions" screen, not some broken default)

No `serializers.py` or `views.py` yet — there's no `/api/accounts/` endpoint. Right now the only way to create a user is `python manage.py createsuperuser` or through `/admin/`. I'll need to add a real registration endpoint once there's a frontend people other than me are supposed to sign up through.

## What's not built here yet

- Registration API (`POST /api/accounts/register/` or similar)
- Token/JWT login for the frontend (currently relying on Django session auth + basic auth, fine for me testing with curl, not fine for a real login page)
- Any notion of teams/organizations — right now it's just individual users, each seeing only their own monitors (enforced over in the `monitors` app, not here)
