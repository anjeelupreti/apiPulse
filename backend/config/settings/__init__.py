import os

# DJANGO_ENV=prod switches to prod.py; everything else (including unset) uses dev.py.
if os.environ.get('DJANGO_ENV') == 'prod':
    from .prod import *  # noqa: F401,F403
else:
    from .dev import *  # noqa: F401,F403
